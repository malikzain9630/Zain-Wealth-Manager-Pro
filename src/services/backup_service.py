"""
Backup Service
Handles database backup and restore.
"""

import shutil
from datetime import datetime
from pathlib import Path

from database import get_connection
from services.settings_service import get_backup_folder_path


def get_project_root():
    """
    Return project root path.
    """

    return Path(__file__).resolve().parent.parent.parent


def get_database_path():
    """
    Detect active SQLite database file path from current connection.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("PRAGMA database_list")
    databases = cur.fetchall()

    conn.close()

    for db in databases:

        if db[1] == "main":

            db_path = db[2]

            if db_path:
                return Path(db_path)

    raise FileNotFoundError(
        "SQLite database file path could not be detected."
    )


def create_backup():
    """
    Create database backup in selected backup folder.
    Returns backup file path.
    """

    db_path = get_database_path()

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database file not found: {db_path}"
        )

    backup_dir = get_backup_folder_path()
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_file = backup_dir / f"zain_wealth_backup_{timestamp}.db"

    shutil.copy2(db_path, backup_file)

    return backup_file


def restore_backup(backup_file_path):
    """
    Restore database from selected backup file.
    """

    backup_file = Path(backup_file_path)

    if not backup_file.exists():
        raise FileNotFoundError(
            "Selected backup file does not exist."
        )

    if backup_file.suffix.lower() not in [".db", ".sqlite", ".sqlite3"]:
        raise ValueError(
            "Invalid backup file. Please select a SQLite database backup file."
        )

    db_path = get_database_path()

    shutil.copy2(backup_file, db_path)

    return db_path