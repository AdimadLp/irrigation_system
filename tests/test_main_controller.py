import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import signal
from app.main import MainController
from app.services.sensor_service import SensorService
from app.services.irrigation_service import IrrigationService
from app.services.database_service import DatabaseService


@pytest.mark.asyncio
class TestMainController:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.controller = MainController(test_mode=True)
        self.controller.stop_event = asyncio.Event()
        self.controller.sensor_service = AsyncMock(spec=SensorService)
        self.controller.irrigation_service = AsyncMock(spec=IrrigationService)
        self.controller.database_service = AsyncMock(spec=DatabaseService)

    @patch("app.main.logger")
    async def test_handle_shutdown(self, mock_logger):
        with patch.object(self.controller, "stop_services", new_callable=AsyncMock):
            self.controller.handle_shutdown(signal.SIGINT, None)
            mock_logger.info.assert_called_with(
                "Received signal 2. Initiating shutdown..."
            )
            await asyncio.sleep(0)  # Yield control to the event loop
            self.controller.stop_services.assert_awaited_once()

    @patch("app.main.db_connection.connect", new_callable=AsyncMock)
    @patch(
        "app.main.IrrigationControllers.check_and_save_controller",
        new_callable=AsyncMock,
    )
    async def test_initialize(self, mock_check_and_save_controller, mock_connect):
        mock_check_and_save_controller.return_value = 1
        await self.controller.initialize()
        mock_connect.assert_awaited_once()
        mock_check_and_save_controller.assert_awaited_once()

    @patch(
        "app.main.IrrigationControllers.check_and_save_controller",
        new_callable=AsyncMock,
    )
    async def test_initialize_controller(self, mock_check_and_save_controller):
        mock_check_and_save_controller.return_value = 1
        controller_id = await self.controller.initialize_controller()
        assert controller_id == 1
        mock_check_and_save_controller.assert_awaited_once()

    @patch("app.main.logger")
    @patch("app.main.MainController.start_services", new_callable=AsyncMock)
    @patch("app.main.MainController.check_service_health", new_callable=AsyncMock)
    @patch("app.main.MainController.monitor_health", new_callable=AsyncMock)
    async def test_run(
        self,
        mock_monitor_health,
        mock_check_service_health,
        mock_start_services,
        mock_logger,
    ):
        async def run_test():
            loop = asyncio.get_running_loop()
            loop.call_later(
                0.1, self.controller.stop_event.set
            )  # Stop the loop after a short delay
            await self.controller.run()

        await run_test()

        mock_start_services.assert_awaited_once()
        mock_check_service_health.assert_awaited()
        mock_monitor_health.assert_awaited()
        mock_logger.error.assert_not_called()

    @patch("app.main.logger")
    async def test_stop_services(self, mock_logger):
        await self.controller.stop_services()
        mock_logger.info.assert_called_with("Stopping all services...")

    @patch("app.main.MainController.stop_services", new_callable=AsyncMock)
    @patch("app.main.MainController.start_services", new_callable=AsyncMock)
    async def test_restart_all_services(self, mock_start_services, mock_stop_services):
        await self.controller.restart_all_services()
        mock_stop_services.assert_awaited_once()
        mock_start_services.assert_awaited_once()

    @patch("app.main.MainController.wait_until_all_healthy", new_callable=AsyncMock)
    async def test_wait_until_all_healthy(self, mock_wait_until_all_healthy):
        await self.controller.wait_until_all_healthy()
        mock_wait_until_all_healthy.assert_awaited_once()

    @patch("app.main.MainController.monitor_health", new_callable=AsyncMock)
    async def test_monitor_health(self, mock_monitor_health):
        await self.controller.monitor_health()
        mock_monitor_health.assert_awaited_once()


if __name__ == "__main__":
    pytest.main()
