"""
Core utility functions
"""
from typing import Optional
import re
from decimal import Decimal


def format_currency(amount: Decimal, currency: str = 'KES') -> str:
    """
    Format currency amount with symbol
    
    Args:
        amount: Decimal amount
        currency: Currency code (KES, USD, EUR, GBP)
    
    Returns:
        Formatted currency string
    """
    symbols = {
        'KES': 'KSh',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
    }
    
    symbol = symbols.get(currency, currency)
    return f"{symbol} {amount:,.2f}"


def format_phone_number(phone: str) -> str:
    """
    Format phone number to E.164 format for Kenya
    
    Args:
        phone: Phone number in various formats
    
    Returns:
        Formatted phone number (254XXXXXXXXX)
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Remove leading zeros
    digits = digits.lstrip('0')
    
    # Add country code if not present
    if not digits.startswith('254'):
        digits = '254' + digits
    
    return digits


def validate_phone_number(phone: str) -> bool:
    """
    Validate Kenyan phone number
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        formatted = format_phone_number(phone)
        # Kenya phone numbers are 12 digits: 254 + 9 digits
        return len(formatted) == 12 and formatted.startswith('254')
    except:
        return False


def generate_receipt_number(prefix: str = 'JR', year: Optional[int] = None, month: Optional[int] = None, sequence: int = 1) -> str:
    """
    Generate receipt number
    
    Args:
        prefix: Receipt prefix
        year: Year (defaults to current)
        month: Month (defaults to current)
        sequence: Sequence number
    
    Returns:
        Receipt number (e.g., JR-2024-11-0001)
    """
    from datetime import datetime
    
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    return f"{prefix}-{year}-{month:02d}-{sequence:04d}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove special characters
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove special characters, keep alphanumeric, dots, dashes, underscores
    sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized


def truncate_text(text: str, length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def calculate_age(birth_date) -> int:
    """
    Calculate age from birth date
    
    Args:
        birth_date: Date of birth
    
    Returns:
        Age in years
    """
    from datetime import date
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def parse_money_amount(amount_str: str) -> Optional[Decimal]:
    """
    Parse money amount from string
    
    Args:
        amount_str: String like "$100", "KSh 1,000", "50.00"
    
    Returns:
        Decimal amount or None if invalid
    """
    try:
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d\.]', '', amount_str)
        return Decimal(cleaned)
    except:
        return None


def get_client_ip(request) -> str:
    """
    Get client IP address from request
    
    Args:
        request: Django request object
    
    Returns:
        IP address string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def slugify_text(text: str) -> str:
    """
    Convert text to slug format
    
    Args:
        text: Text to slugify
    
    Returns:
        Slugified text
    """
    from django.utils.text import slugify
    return slugify(text)


# Date utilities
def format_date(date_obj, format_str: str = '%Y-%m-%d') -> str:
    """Format date object to string"""
    if date_obj:
        return date_obj.strftime(format_str)
    return ''


def format_datetime(datetime_obj, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime object to string"""
    if datetime_obj:
        return datetime_obj.strftime(format_str)
    return ''
