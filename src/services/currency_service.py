"""
Currency Service
Handles multi-currency display and conversion.

Important rule:
- Database values remain stored in PKR.
- Display conversion happens only while showing values in GUI/reports.
- Exchange rates are stored as:
    1 unit of selected currency = X PKR

Example:
    USD to PKR rate = 280
    PKR 280,000 / 280 = USD 1,000
"""

from services.settings_service import load_settings


BASE_CURRENCY = "PKR"
DEFAULT_DISPLAY_CURRENCY = "PKR"

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

DEFAULT_EXCHANGE_RATES_TO_PKR = {
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

CURRENCY_NAMES = {
    "PKR": "Pakistani Rupee",
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "SAR": "Saudi Riyal",
    "AED": "UAE Dirham",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "JPY": "Japanese Yen",
    "CNY": "Chinese Yuan",
}

CURRENCY_SYMBOLS = {
    "PKR": "PKR",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "SAR": "SAR",
    "AED": "AED",
    "CAD": "C$",
    "AUD": "A$",
    "JPY": "¥",
    "CNY": "¥",
}


def get_supported_currencies():
    """
    Return supported display currencies.
    """

    return SUPPORTED_CURRENCIES.copy()


def get_currency_name(currency_code):
    """
    Return full currency name.
    """

    currency_code = normalize_currency(currency_code)

    return CURRENCY_NAMES.get(currency_code, currency_code)


def get_currency_symbol(currency_code=None):
    """
    Return currency symbol/code for display.
    """

    if currency_code is None:
        currency_code = get_display_currency()

    currency_code = normalize_currency(currency_code)

    return CURRENCY_SYMBOLS.get(currency_code, currency_code)


def normalize_currency(currency_code):
    """
    Normalize and validate currency code.
    """

    currency_code = str(currency_code or DEFAULT_DISPLAY_CURRENCY).strip().upper()

    if currency_code not in SUPPORTED_CURRENCIES:
        currency_code = DEFAULT_DISPLAY_CURRENCY

    return currency_code


def get_currency_settings():
    """
    Return currency-related settings safely.

    Supported settings keys:
        currency:
            selected display currency

        exchange_rates:
            dictionary of rates to PKR

        usd_to_pkr_rate:
            legacy support for old settings
    """

    settings = load_settings()

    display_currency = normalize_currency(
        settings.get("currency", DEFAULT_DISPLAY_CURRENCY)
    )

    exchange_rates = DEFAULT_EXCHANGE_RATES_TO_PKR.copy()

    stored_rates = settings.get("exchange_rates", {})

    if isinstance(stored_rates, dict):

        for currency_code, rate in stored_rates.items():

            currency_code = normalize_currency(currency_code)

            rate = safe_float(rate)

            if rate > 0:
                exchange_rates[currency_code] = rate

    # Backward compatibility with old USD-only setting.
    legacy_usd_rate = safe_float(
        settings.get("usd_to_pkr_rate", 0)
    )

    if legacy_usd_rate > 0:
        exchange_rates["USD"] = legacy_usd_rate

    exchange_rates["PKR"] = 1.0

    return {
        "base_currency": BASE_CURRENCY,
        "display_currency": display_currency,
        "exchange_rates": exchange_rates,
    }


def get_display_currency():
    """
    Return selected display currency.
    """

    return get_currency_settings()["display_currency"]


def get_exchange_rate_to_pkr(currency_code=None):
    """
    Return exchange rate:
        1 selected currency = X PKR
    """

    if currency_code is None:
        currency_code = get_display_currency()

    currency_code = normalize_currency(currency_code)

    settings = get_currency_settings()
    exchange_rates = settings["exchange_rates"]

    rate = safe_float(
        exchange_rates.get(
            currency_code,
            DEFAULT_EXCHANGE_RATES_TO_PKR.get(currency_code, 1.0)
        )
    )

    if rate <= 0:
        rate = DEFAULT_EXCHANGE_RATES_TO_PKR.get(currency_code, 1.0)

    return rate


def convert_from_pkr(amount, currency_code=None):
    """
    Convert PKR amount to selected display currency.

    If selected currency is PKR:
        returns amount as-is

    If selected currency is USD:
        returns amount / USD_TO_PKR_RATE

    Same formula applies to all supported currencies.
    """

    amount = safe_float(amount)

    if currency_code is None:
        currency_code = get_display_currency()

    currency_code = normalize_currency(currency_code)

    if currency_code == "PKR":
        return amount

    rate_to_pkr = get_exchange_rate_to_pkr(currency_code)

    if rate_to_pkr <= 0:
        return amount

    return amount / rate_to_pkr


def convert_to_pkr(amount, currency_code=None):
    """
    Convert amount from selected/input currency back to PKR.

    Example:
        USD 1,000 * 280 = PKR 280,000
    """

    amount = safe_float(amount)

    if currency_code is None:
        currency_code = get_display_currency()

    currency_code = normalize_currency(currency_code)

    if currency_code == "PKR":
        return amount

    rate_to_pkr = get_exchange_rate_to_pkr(currency_code)

    return amount * rate_to_pkr


def format_currency(amount, currency_code=None, use_symbol=False):
    """
    Format PKR amount according to selected display currency.

    Database amount must be supplied in PKR.
    """

    if currency_code is None:
        currency_code = get_display_currency()

    currency_code = normalize_currency(currency_code)
    converted_amount = convert_from_pkr(amount, currency_code)

    if use_symbol:
        prefix = get_currency_symbol(currency_code)
    else:
        prefix = currency_code

    return f"{prefix} {converted_amount:,.2f}"


def format_currency_with_rate(amount, currency_code=None):
    """
    Format amount and include conversion rate note if not PKR.
    Useful for reports/tooltips/messages.
    """

    if currency_code is None:
        currency_code = get_display_currency()

    currency_code = normalize_currency(currency_code)
    formatted_amount = format_currency(amount, currency_code)

    if currency_code != "PKR":
        rate = get_exchange_rate_to_pkr(currency_code)
        return f"{formatted_amount} @ {rate:,.2f} PKR/{currency_code}"

    return formatted_amount


def get_conversion_note(currency_code=None):
    """
    Return conversion note for UI/reports.
    """

    if currency_code is None:
        currency_code = get_display_currency()

    currency_code = normalize_currency(currency_code)

    if currency_code == "PKR":
        return "Base currency: PKR"

    rate = get_exchange_rate_to_pkr(currency_code)

    return f"Display currency: {currency_code} | 1 {currency_code} = PKR {rate:,.2f}"


def safe_float(value):
    """
    Convert value to float safely.
    """

    try:
        if value is None:
            return 0.0

        return float(value)

    except (ValueError, TypeError):
        return 0.0
