"""
Database Backup System
"""

from pathlib import Path
from shutil import copy2
from datetime import datetime

from logger import info

DB_FILE = Path(__file__).resolve().parent.parent / "wealth_manager.db"

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backup"
BACKUP_DIR.mkdir(exist_ok=True)


def create_backup():

    if not DB_FILE.exists():
        print("No database found to backup.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_file = BACKUP_DIR / f"wealth_manager_{timestamp}.db"

    copy2(DB_FILE, backup_file)

    message = f"Backup Created: {backup_file.name}"

    print(message)
    info(message)

    return backup_file