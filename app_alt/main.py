import signal
import threading
import redis
import sys
import time
from logging_config import setup_logger
from services.irrigation_service import IrrigationService
from services.sensor_service import SensorService
from services.database_service import DatabaseService
from database.models import IrrigationControllers

logger = setup_logger("main")


class MainController:
    def __init__(self):
        self.controller_id = self.initialize_controller()
        self.stop_event = threading.Event()
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0)
        self.sensor_service = SensorService(
            self.controller_id, self.redis_client, self.stop_event
        )
        self.irrigation_service = IrrigationService(
            self.controller_id, self.redis_client, self.stop_event
        )
        self.database_service = DatabaseService(
            self.controller_id,
            self.redis_client,
            self.sensor_service,
            self.irrigation_service,
            self.stop_event,
        )
        self.last_restart_time = None

    def initialize_controller(self):
        return IrrigationControllers.check_and_save_controller()

    def start_services(self):
        logger.info("Starting all services...")
        for service in [
            self.sensor_service,
            self.irrigation_service,
            self.database_service,
        ]:
            service.start()

    def stop_services(self):
        logger.info("Stopping all services...")
        self.stop_event.set()  # Signal all services to stop
        for service in [
            self.sensor_service,
            self.irrigation_service,
            self.database_service,
        ]:
            service.stop()

    def check_service_health(self):
        services = [
            (self.sensor_service, "Sensor"),
            (self.irrigation_service, "Irrigation"),
            (self.database_service, "Database"),
        ]
        restart_needed = False

        for service, name in services:
            if not service.is_healthy():
                logger.warning(f"{name} service unhealthy. Attempting restart.")
                service.restart()

                # Warte nicht sofort, sondern verwende self.stop_event.wait() für 1 Minute
                if not self.stop_event.wait(
                    60
                ):  # Warten Sie 1 Minute (60 Sekunden), um zu sehen, ob der Dienst sich erholt hat
                    if not service.is_healthy():
                        logger.error(f"{name} service restart failed.")
                        restart_needed = True

        if restart_needed:
            logger.error("Full service restart required.")
            self.restart_all_services()

    def restart_all_services(self):
        """Neustart aller Dienste und Überwachung für 1 Stunde."""
        self.stop_services()
        self.start_services()

        # Setze den Zeitpunkt des Neustarts
        self.last_restart_time = time.time()

        # Verwende self.stop_event.wait() statt time.sleep() nach dem Neustart aller Dienste
        if not self.stop_event.wait(
            60
        ):  # 1 Minute warten, um zu sehen, ob die Dienste sich stabilisieren
            # Nach dem Neustart die Dienste erneut überprüfen
            if not (
                self.sensor_service.is_healthy()
                and self.irrigation_service.is_healthy()
                and self.database_service.is_healthy()
            ):
                logger.critical("Restart of all services failed. Exiting with failure.")
                sys.exit(1)

    def monitor_health(self):
        """Überwacht den Gesundheitszustand und beendet, wenn innerhalb einer Stunde nach dem Neustart wieder Fehler auftreten."""
        # Überprüfe, ob der letzte Neustart innerhalb der letzten Stunde war
        if self.last_restart_time and time.time() - self.last_restart_time < 3600:
            services = [
                (self.sensor_service, "Sensor"),
                (self.irrigation_service, "Irrigation"),
                (self.database_service, "Database"),
            ]

            # Falls irgendein Dienst wieder ungesund ist, Programm beenden
            for service, name in services:
                if not service.is_healthy():
                    logger.critical(
                        f"{name} service became unhealthy again within one hour after restart. Exiting."
                    )
                    sys.exit(1)

    def handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}. Initiating shutdown...")
        self.stop_event.set()

    def run(self):
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

        self.start_services()

        try:
            while not self.stop_event.is_set():
                self.check_service_health()
                self.monitor_health()
                self.stop_event.wait(10)

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop_services()
            logger.info("All services stopped. Exiting.")


def main():
    try:
        controller = MainController()
        controller.run()
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
    finally:
        logger.info("Program terminated.")


if __name__ == "__main__":
    main()
