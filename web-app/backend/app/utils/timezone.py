"""
Timezone utilities for the Web Invoice Processor application.

This module provides utilities for handling timezone conversions,
specifically for Beijing time (Asia/Shanghai).
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# Beijing timezone (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """
    Get current datetime in Beijing timezone.
    
    Returns:
        Current datetime with Beijing timezone info
    """
    return datetime.now(BEIJING_TZ)


def utc_to_beijing(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to Beijing timezone.
    
    Args:
        utc_dt: UTC datetime (timezone-aware or naive)
        
    Returns:
        Datetime converted to Beijing timezone
    """
    if utc_dt.tzinfo is None:
        # Assume naive datetime is UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    return utc_dt.astimezone(BEIJING_TZ)


def beijing_to_utc(beijing_dt: datetime) -> datetime:
    """
    Convert Beijing datetime to UTC timezone.
    
    Args:
        beijing_dt: Beijing datetime (timezone-aware or naive)
        
    Returns:
        Datetime converted to UTC timezone
    """
    if beijing_dt.tzinfo is None:
        # Assume naive datetime is Beijing time
        beijing_dt = beijing_dt.replace(tzinfo=BEIJING_TZ)
    
    return beijing_dt.astimezone(timezone.utc)


def format_beijing_time(dt: datetime, format_str: Optional[str] = None) -> str:
    """
    Format datetime as Beijing time string.
    
    Args:
        dt: Datetime to format
        format_str: Optional format string (default: ISO format)
        
    Returns:
        Formatted datetime string in Beijing timezone
    """
    beijing_dt = utc_to_beijing(dt) if dt.tzinfo != BEIJING_TZ else dt
    
    if format_str:
        return beijing_dt.strftime(format_str)
    else:
        # Return ISO format with timezone info
        return beijing_dt.isoformat()