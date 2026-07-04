"""
Settings Service
Handles application settings save/load.
"""

import json
from pathlib import Path


DEFAULT_SETTINGS = {
    "currency": "PKR",
    "concentration_limit": 30,
    "backup_folder": "backups",
    "theme": "light",
    "auto_refresh": False
}


def get_project_root():
    """
    Return project root path.
    """

    return Path(__file__).resolve().parent.parent.parent


def get_config_dir():
    """
    Return config directory path.
    """

    config_dir = get_project_root() / "config"
    config_dir.mkdir(exist_ok=True)

    return config_dir


def get_settings_file():
    """
    Return settings.json file path.
    """

    return get_config_dir() / "settings.json"


def create_default_settings():
    """
    Create default settings file.
    """

    settings_file = get_settings_file()

    with open(settings_file, "w", encoding="utf-8") as file:
        json.dump(DEFAULT_SETTINGS, file, indent=4)

    return DEFAULT_SETTINGS.copy()


def load_settings():
    """
    Load settings from settings.json.
    If file does not exist, create it with default settings.
    """

    settings_file = get_settings_file()

    if not settings_file.exists():
        return create_default_settings()

    try:
        with open(settings_file, "r", encoding="utf-8") as file:
            settings = json.load(file)

    except json.JSONDecodeError:
        settings = DEFAULT_SETTINGS.copy()
        save_settings(settings)
        return settings

    updated = False

    for key, value in DEFAULT_SETTINGS.items():

        if key not in settings:
            settings[key] = value
            updated = True

    if updated:
        save_settings(settings)

    return settings


def save_settings(settings):
    """
    Save settings to settings.json.
    """

    settings_file = get_settings_file()

    with open(settings_file, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)

    return settings


def get_setting(key):
    """
    Get a single setting value.
    """

    settings = load_settings()

    if key in settings:
        return settings[key]

    return DEFAULT_SETTINGS.get(key)


def update_setting(key, value):
    """
    Update a single setting value.
    """

    settings = load_settings()
    settings[key] = value

    save_settings(settings)

    return settings


def update_settings(new_settings):
    """
    Update multiple settings at once.
    """

    settings = load_settings()

    for key, value in new_settings.items():
        settings[key] = value

    save_settings(settings)

    return settings


def reset_settings():
    """
    Reset all settings to default values.
    """

    return create_default_settings()


def get_currency():
    """
    Return selected currency.
    """

    return get_setting("currency")


def get_concentration_limit():
    """
    Return concentration alert limit.
    """

    try:
        return float(get_setting("concentration_limit"))

    except (ValueError, TypeError):
        return float(DEFAULT_SETTINGS["concentration_limit"])


def get_backup_folder():
    """
    Return backup folder setting.
    """

    folder = get_setting("backup_folder")

    if not folder:
        folder = DEFAULT_SETTINGS["backup_folder"]

    return folder


def get_backup_folder_path():
    """
    Return full backup folder path.
    """

    folder = get_backup_folder()

    folder_path = Path(folder)

    if folder_path.is_absolute():
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    full_path = get_project_root() / folder
    full_path.mkdir(parents=True, exist_ok=True)

    return full_path