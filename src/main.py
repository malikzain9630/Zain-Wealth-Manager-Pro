"""
Zain Wealth Manager Pro
Main Entry Point
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent

sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(SRC_DIR))

from database import initialize_database
from gui import MainWindow


def main():
    """
    Start GUI application.
    """

    initialize_database()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()