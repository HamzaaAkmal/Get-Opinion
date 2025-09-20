"""
Helper utilities and common functions
Contains various utility functions used across the application
"""
import re
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional


def generate_batch_id(length: int = 8) -> str:
    """Generate a unique batch ID"""
    return str(uuid.uuid4())[:length]


def get_current_timestamp() -> str:
    """Get current timestamp in standard format"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def get_current_iso_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def format_number(number: int) -> str:
    """Format a number with thousand separators"""
    return f"{number:,}"


def calculate_percentage(part: int, total: int) -> float:
    """Calculate percentage with safe division"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove or replace problematic characters
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Truncate if necessary
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    return text.strip()


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract meaningful keywords from text"""
    if not text:
        return []
    
    # Convert to lowercase and split
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out short words and common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
        'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    return list(set(keywords))  # Remove duplicates


def validate_query(query: str) -> tuple[bool, str]:
    """Validate a search query"""
    if not query or not query.strip():
        return False, "Query cannot be empty"
    
    query = query.strip()
    
    if len(query) < 2:
        return False, "Query must be at least 2 characters long"
    
    if len(query) > 500:
        return False, "Query must be less than 500 characters"
    
    # Check for potentially problematic patterns
    if re.search(r'[<>\"\'&]', query):
        return False, "Query contains invalid characters"
    
    return True, "Query is valid"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dictionaries(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def rate_limit_pause(calls_made: int, calls_per_minute: int = 60) -> None:
    """Implement rate limiting by pausing execution"""
    if calls_made > 0 and calls_made % calls_per_minute == 0:
        pause_seconds = 60  # Pause for 1 minute after hitting the limit
        print(f"⏳ Rate limit reached ({calls_per_minute} calls/min). Pausing for {pause_seconds} seconds...")
        time.sleep(pause_seconds)


def calculate_eta(processed: int, total: int, start_time: float) -> str:
    """Calculate estimated time of arrival for a process"""
    if processed == 0:
        return "Calculating..."
    
    elapsed = time.time() - start_time
    rate = processed / elapsed
    remaining = total - processed
    
    if rate > 0:
        eta_seconds = remaining / rate
        return format_duration(eta_seconds)
    else:
        return "Unknown"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def extract_video_id_from_url(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def sanitize_for_api(text: str) -> str:
    """Sanitize text for API calls"""
    if not text:
        return ""
    
    # Remove or escape problematic characters
    text = text.replace('"', '\\"')
    text = text.replace("'", "\\'")
    text = re.sub(r'[^\w\s\-_.,!?]', '', text)
    
    return text.strip()


def create_progress_indicator(current: int, total: int, width: int = 50) -> str:
    """Create a text-based progress bar"""
    if total == 0:
        return "[" + " " * width + "] 0%"
    
    percentage = current / total
    filled_width = int(width * percentage)
    bar = "█" * filled_width + "░" * (width - filled_width)
    
    return f"[{bar}] {percentage * 100:.1f}%"


def log_performance_metrics(operation_name: str, start_time: float, 
                          items_processed: int = 0, **kwargs) -> None:
    """Log performance metrics for operations"""
    elapsed = time.time() - start_time
    
    print(f"⏱️  Performance metrics for '{operation_name}':")
    print(f"   Duration: {format_duration(elapsed)}")
    
    if items_processed > 0:
        rate = items_processed / elapsed
        print(f"   Items processed: {format_number(items_processed)}")
        print(f"   Processing rate: {rate:.2f} items/second")
    
    for key, value in kwargs.items():
        print(f"   {key}: {value}")


def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0, 
                    backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Decorator for retrying function calls on failure"""
    def wrapper(*args, **kwargs):
        current_delay = delay
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_retries:
                    print(f"❌ Function {func.__name__} failed after {max_retries + 1} attempts: {e}")
                    raise
                
                print(f"⚠️  Attempt {attempt + 1} failed for {func.__name__}: {e}")
                print(f"   Retrying in {current_delay:.1f} seconds...")
                time.sleep(current_delay)
                current_delay *= backoff
        
        return None
    
    return wrapper