"""
Database Restore System
"""

from pathlib import Path
from shutil import copy2
from logger import info

DB_FILE = Path(__file__).resolve().parent.parent / "wealth_manager.db"

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backup"


def list_backups():

    files = sorted(BACKUP_DIR.glob("*.db"))

    return files


def restore_backup(filename):

    backup_file = BACKUP_DIR / filename

    if not backup_file.exists():
        print("Backup file not found.")
        return

    copy2(backup_file, DB_FILE)

    message = "Database restored successfully."

print(message)

info(message)