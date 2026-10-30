"""Parsing and rounding of Toman amounts typed by users or returned by Wallex."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_SEPARATORS = (",", "٬", "،", " ", "‌", " ")


def normalize_digits(text):
    """Convert Persian and Arabic-Indic digits to Western digits."""
    return text.translate(_DIGITS)


def parse_toman(text):
    """Parse a whole Toman amount such as "۲۷۱٬۱۶۵" or "271,165" into a Decimal.

    Raises ValueError for empty, non-numeric or fractional input.
    """
    if text is None:
        raise ValueError("empty")
    cleaned = normalize_digits(str(text)).strip()
    for sep in _SEPARATORS:
        cleaned = cleaned.replace(sep, "")
    if not cleaned or not (cleaned.lstrip("-").isdigit()):
        raise ValueError(f"not a whole number: {text!r}")
    return Decimal(cleaned)


def round_toman(value):
    """Round to the nearest whole Toman, halves rounded up (FR-006)."""
    try:
        return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"not a number: {value!r}") from exc
