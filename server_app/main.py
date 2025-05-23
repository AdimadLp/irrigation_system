import asyncio
import signal
from server_app.logging_config import setup_logger
from irrigation_controller.irrigation_service import IrrigationService
from irrigation_controller.sensor_service import SensorService
from server_app.services.database_service import DatabaseService
from server_app.database.models import IrrigationControllers
import traceback
from server_app.database.database import db_connection
import argparse

logger = setup_logger("main")


class MainController:
    def __init__(self, test_mode=False):
        self.controller_id = None
        self.stop_event = asyncio.Event()
        self.sensor_service = None
        self.irrigation_service = None
        self.database_service = None
        self.last_restart_time = None
        self.test_mode = test_mode

    @classmethod
    async def create(cls, test_mode=False):
        self = cls(test_mode)
        await self.initialize()
        return self

    async def initialize(self):
        await db_connection.connect()
        self.controller_id = await self.initialize_controller()
        self.sensor_service = SensorService(
            self.controller_id, self.stop_event, self.test_mode
        )
        self.irrigation_service = IrrigationService(
            self.controller_id, self.stop_event, self.test_mode
        )
        self.database_service = DatabaseService(
            self.controller_id,
            self.sensor_service,
            self.irrigation_service,
            self.stop_event,
        )

    async def initialize_controller(self):
        try:
            return await IrrigationControllers.check_and_save_controller()
        except Exception as e:
            logger.error(f"Error initializing controller: {str(e)}")

    async def start_services(self):
        logger.info("Starting all services...")
        try:
            await asyncio.gather(
                self.sensor_service.start(),
                self.irrigation_service.start(),
                self.database_service.start(),
            )
        except Exception as e:
            logger.error(f"Failed to start all services: {str(e)}")

    async def stop_services(self):
        logger.info("Stopping all services...")
        self.stop_event.set()
        await asyncio.gather(
            self.sensor_service.stop(),
            self.irrigation_service.stop(),
            self.database_service.stop(),
        )

    async def check_service_health(self):
        services = [
            (self.sensor_service, "Sensor"),
            (self.irrigation_service, "Irrigation"),
            (self.database_service, "Database"),
        ]

        async def check_and_restart(service, name):
            if not await service.is_healthy():
                logger.warning(f"{name} service unhealthy. Attempting restart.")
                await service.stop()
                await service.start()
                try:
                    await asyncio.wait_for(service.wait_until_healthy(), timeout=60)
                except asyncio.TimeoutError:
                    logger.error(f"{name} service restart failed.")
                    return False
            return True

        results = await asyncio.gather(
            *(check_and_restart(service, name) for service, name in services)
        )

        if not all(results):
            logger.error("Full service restart required.")
            await self.restart_all_services()

    async def restart_all_services(self):
        await self.stop_services()
        await self.start_services()
        self.last_restart_time = asyncio.get_running_loop().time()

        try:
            await asyncio.wait_for(self.wait_until_all_healthy(), timeout=60)
        except asyncio.TimeoutError:
            logger.critical("Restart of all services failed. Exiting with failure.")
            asyncio.get_running_loop().stop()

    async def wait_until_all_healthy(self):
        await asyncio.gather(
            self.sensor_service.wait_until_healthy(),
            self.irrigation_service.wait_until_healthy(),
            self.database_service.wait_until_healthy(),
        )

    async def monitor_health(self):
        if (
            self.last_restart_time
            and asyncio.get_running_loop().time() - self.last_restart_time < 3600
        ):
            services = [
                (self.sensor_service, "Sensor"),
                (self.irrigation_service, "Irrigation"),
                (self.database_service, "Database"),
            ]

            unhealthy = [
                name for service, name in services if not await service.is_healthy()
            ]
            if unhealthy:
                logger.critical(
                    f"{', '.join(unhealthy)} service(s) became unhealthy again within one hour after restart. Exiting."
                )
                asyncio.get_running_loop().stop()

    def handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}. Initiating shutdown...")
        asyncio.create_task(self.stop_services())

    async def run(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            asyncio.get_running_loop().add_signal_handler(
                sig, self.handle_shutdown, sig, None
            )

        try:
            await self.start_services()

            while not self.stop_event.is_set():
                try:
                    await self.check_service_health()
                    await self.monitor_health()
                    await asyncio.sleep(10)
                except Exception as e:
                    logger.error(f"Error in main loop: {str(e)}")
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                    await asyncio.sleep(5)  # Wait before retrying
        except Exception as e:
            logger.critical(f"Critical error in run method: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
        finally:
            await self.stop_services()
            logger.info("All services stopped. Exiting.")


async def main():
    parser = argparse.ArgumentParser(description="Irrigation System Controller")
    parser.add_argument(
        "-test", action="store_true", help="Run the controller in test mode"
    )
    args = parser.parse_args()

    if args.test:
        logger.info("Starting the controller in test mode.")
    else:
        logger.info("Starting the controller in normal mode.")

    try:
        controller = await MainController.create(test_mode=args.test)
        await controller.run()
    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
    finally:
        logger.info("Program terminated.")


if __name__ == "__main__":
    asyncio.run(main())
