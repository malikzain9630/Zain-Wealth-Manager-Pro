"""
Settings Service
Handles application settings.

Settings are stored in:
    src/config/settings.json

Important:
- Portfolio/database values remain stored in PKR.
- Currency setting only controls display currency.
- Exchange rates are stored as:
    1 selected currency = X PKR
"""

import json
from pathlib import Path


SUPPORTED_CURRENCIES = [
    "PKR",
    "USD",
    "EUR",
    "GBP",
    "SAR",
    "AED",
    "CAD",
    "AUD",
    "JPY",
    "CNY",
]

DEFAULT_EXCHANGE_RATES = {
    "PKR": 1.0,
    "USD": 280.0,
    "EUR": 305.0,
    "GBP": 360.0,
    "SAR": 74.5,
    "AED": 76.25,
    "CAD": 205.0,
    "AUD": 185.0,
    "JPY": 1.90,
    "CNY": 39.0,
}


def get_settings_file():
    """
    Return settings file path.
    """

    src_folder = Path(__file__).resolve().parent.parent
    config_folder = src_folder / "config"
    config_folder.mkdir(parents=True, exist_ok=True)

    return config_folder / "settings.json"


def get_default_settings():
    """
    Return default settings.
    """

    src_folder = Path(__file__).resolve().parent.parent
    project_root = src_folder.parent

    return {
        "currency": "PKR",
        "theme": "light",
        "concentration_limit": 30,
        "backup_folder": str(project_root / "backups"),
        "exchange_rates": DEFAULT_EXCHANGE_RATES.copy(),
        # Legacy key kept for compatibility with older files/code.
        "usd_to_pkr_rate": DEFAULT_EXCHANGE_RATES["USD"],
    }


def load_settings():
    """
    Load settings from JSON file.

    If file is missing or invalid, defaults are returned.
    Missing keys are auto-filled from defaults.
    """

    settings_file = get_settings_file()
    default_settings = get_default_settings()

    if not settings_file.exists():
        save_settings(default_settings)
        return default_settings

    try:
        with open(settings_file, "r", encoding="utf-8") as file:
            saved_settings = json.load(file)

    except Exception:
        save_settings(default_settings)
        return default_settings

    if not isinstance(saved_settings, dict):
        save_settings(default_settings)
        return default_settings

    merged_settings = merge_settings(default_settings, saved_settings)

    # Save back only if new keys were added or invalid values were fixed.
    save_settings(merged_settings)

    return merged_settings


def merge_settings(default_settings, saved_settings):
    """
    Merge saved settings with defaults safely.
    """

    merged = default_settings.copy()

    for key, value in saved_settings.items():

        if key == "exchange_rates":
            continue

        merged[key] = value

    saved_rates = saved_settings.get("exchange_rates", {})

    merged_rates = DEFAULT_EXCHANGE_RATES.copy()

    if isinstance(saved_rates, dict):

        for currency_code, rate in saved_rates.items():

            currency_code = normalize_currency(currency_code)

            rate = safe_float(rate)

            if rate > 0:
                merged_rates[currency_code] = rate

    # Legacy USD-only support.
    legacy_usd_rate = safe_float(
        saved_settings.get("usd_to_pkr_rate", 0)
    )

    if legacy_usd_rate > 0:
        merged_rates["USD"] = legacy_usd_rate

    merged_rates["PKR"] = 1.0

    merged["exchange_rates"] = merged_rates
    merged["currency"] = normalize_currency(
        merged.get("currency", "PKR")
    )
    merged["theme"] = normalize_theme(
        merged.get("theme", "light")
    )
    merged["concentration_limit"] = safe_float(
        merged.get("concentration_limit", 30),
        30
    )
    merged["usd_to_pkr_rate"] = merged_rates["USD"]

    backup_folder = str(
        merged.get("backup_folder", default_settings["backup_folder"])
    ).strip()

    if not backup_folder:
        backup_folder = default_settings["backup_folder"]

    merged["backup_folder"] = backup_folder

    return merged


def save_settings(settings):
    """
    Save settings to JSON file.
    """

    settings_file = get_settings_file()
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    cleaned_settings = clean_settings(settings)

    with open(settings_file, "w", encoding="utf-8") as file:
        json.dump(cleaned_settings, file, indent=4)

    return cleaned_settings


def update_settings(new_settings):
    """
    Update and save settings.
    """

    current_settings = load_settings()

    if not isinstance(new_settings, dict):
        return current_settings

    current_settings.update(new_settings)

    updated_settings = clean_settings(current_settings)
    save_settings(updated_settings)

    return updated_settings


def reset_settings():
    """
    Reset settings to default values.
    """

    default_settings = get_default_settings()
    save_settings(default_settings)

    return default_settings


def clean_settings(settings):
    """
    Validate settings before saving.
    """

    default_settings = get_default_settings()

    if not isinstance(settings, dict):
        settings = {}

    cleaned = default_settings.copy()

    for key, value in settings.items():

        if key == "exchange_rates":
            continue

        cleaned[key] = value

    cleaned["currency"] = normalize_currency(
        cleaned.get("currency", "PKR")
    )

    cleaned["theme"] = normalize_theme(
        cleaned.get("theme", "light")
    )

    cleaned["concentration_limit"] = safe_float(
        cleaned.get("concentration_limit", 30),
        30
    )

    backup_folder = str(
        cleaned.get("backup_folder", default_settings["backup_folder"])
    ).strip()

    if not backup_folder:
        backup_folder = default_settings["backup_folder"]

    cleaned["backup_folder"] = backup_folder

    cleaned_rates = DEFAULT_EXCHANGE_RATES.copy()

    exchange_rates = settings.get("exchange_rates", {})

    if isinstance(exchange_rates, dict):

        for currency_code, rate in exchange_rates.items():

            currency_code = normalize_currency(currency_code)
            rate = safe_float(rate)

            if rate > 0:
                cleaned_rates[currency_code] = rate

    legacy_usd_rate = safe_float(
        settings.get("usd_to_pkr_rate", 0)
    )

    if legacy_usd_rate > 0:
        cleaned_rates["USD"] = legacy_usd_rate

    cleaned_rates["PKR"] = 1.0

    cleaned["exchange_rates"] = cleaned_rates
    cleaned["usd_to_pkr_rate"] = cleaned_rates["USD"]

    return cleaned


def get_backup_folder_path():
    """
    Return backup folder path from settings.

    This function is used by backup_service.py.
    Kept for backward compatibility with existing backup system.
    """

    settings = load_settings()

    backup_folder = str(
        settings.get(
            "backup_folder",
            get_default_settings()["backup_folder"]
        )
    ).strip()

    if not backup_folder:
        backup_folder = get_default_settings()["backup_folder"]

    backup_path = Path(backup_folder)
    backup_path.mkdir(parents=True, exist_ok=True)

    return backup_path


def get_currency():
    """
    Return selected display currency.
    Kept for compatibility with older code.
    """

    settings = load_settings()

    return normalize_currency(
        settings.get("currency", "PKR")
    )


def get_theme():
    """
    Return selected theme.
    Kept for compatibility with older code.
    """

    settings = load_settings()

    return normalize_theme(
        settings.get("theme", "light")
    )


def get_concentration_limit():
    """
    Return concentration alert limit.
    Kept for compatibility with older code.
    """

    settings = load_settings()

    return safe_float(
        settings.get("concentration_limit", 30),
        30
    )


def normalize_currency(currency_code):
    """
    Normalize currency code.
    """

    currency_code = str(currency_code or "PKR").strip().upper()

    if currency_code not in SUPPORTED_CURRENCIES:
        currency_code = "PKR"

    return currency_code


def normalize_theme(theme):
    """
    Normalize theme value.
    """

    theme = str(theme or "light").strip().lower()

    if theme not in ["light", "dark"]:
        theme = "light"

    return theme


def safe_float(value, default=0.0):
    """
    Convert value to float safely.
    """

    try:
        if value is None:
            return float(default)

        return float(value)

    except (ValueError, TypeError):
        return float(default)
