import sys
from PyQt6.QtWidgets import QApplication
from ui.ui_manager import UIManager
from application_controller import ApplicationController
from event_bus import EventBus
from config_manager import ConfigManager


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    event_bus = EventBus()
    ConfigManager.initialize(event_bus)
    ui_manager = UIManager(event_bus)

    controller = ApplicationController(ui_manager, event_bus)

    exit_code = controller.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
