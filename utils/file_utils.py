"""
File utilities for saving and loading JSON data
Handles file operations, directory creation, and filename sanitization
"""
import os
import json
from datetime import datetime
from config import Config


def sanitize_filename(filename):
    """Sanitize a string to be safe for use as a filename"""
    if not filename or not filename.strip():
        return "unknown_file"
    
    # Replace spaces with underscores
    sanitized = filename.strip().replace(' ', '_')
    
    # Remove or replace special characters that are problematic in filenames
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c in '_-')
    
    # Remove multiple consecutive underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    
    # Limit length to avoid overly long filenames
    max_length = Config.MAX_FILENAME_LENGTH
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove trailing underscores
    sanitized = sanitized.rstrip('_')
    
    # Ensure we have at least some content
    if not sanitized:
        sanitized = "file"
    
    return sanitized.lower()


def ensure_directory_exists(directory_path):
    """Ensure a directory exists, creating it if necessary"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error creating directory {directory_path}: {e}")
        return False


def save_to_json_file(data, directory, filename_prefix, encoding='utf-8'):
    """Save data to a JSON file with proper error handling"""
    try:
        # Ensure directory exists
        if not ensure_directory_exists(directory):
            return None
        
        # Create full filename
        filename = f"{filename_prefix}.json"
        filepath = os.path.join(directory, filename)
        
        # Save data to file
        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Data saved to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving data to {directory}/{filename_prefix}.json: {e}")
        return None


def load_from_json_file(filepath, encoding='utf-8'):
    """Load data from a JSON file with proper error handling"""
    try:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        with open(filepath, 'r', encoding=encoding) as f:
            data = json.load(f)
        
        print(f"✅ Data loaded from: {filepath}")
        return data
        
    except Exception as e:
        print(f"❌ Error loading data from {filepath}: {e}")
        return None


def list_json_files(directory, pattern=None):
    """List all JSON files in a directory, optionally filtered by pattern"""
    try:
        if not os.path.exists(directory):
            print(f"❌ Directory not found: {directory}")
            return []
        
        files = []
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                if pattern is None or pattern in filename:
                    filepath = os.path.join(directory, filename)
                    # Get file stats
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files
        
    except Exception as e:
        print(f"❌ Error listing files in {directory}: {e}")
        return []


def get_file_size_mb(filepath):
    """Get file size in megabytes"""
    try:
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)  # Convert to MB
    except Exception as e:
        print(f"❌ Error getting file size for {filepath}: {e}")
        return 0


def cleanup_old_files(directory, max_files=100, file_pattern=None):
    """Clean up old files in a directory, keeping only the newest ones"""
    try:
        files = list_json_files(directory, file_pattern)
        
        if len(files) <= max_files:
            print(f"📁 Directory {directory} has {len(files)} files (within limit of {max_files})")
            return 0
        
        # Delete oldest files
        files_to_delete = files[max_files:]
        deleted_count = 0
        
        for file_info in files_to_delete:
            try:
                os.remove(file_info['filepath'])
                deleted_count += 1
                print(f"🗑️  Deleted old file: {file_info['filename']}")
            except Exception as e:
                print(f"❌ Error deleting {file_info['filename']}: {e}")
        
        print(f"🧹 Cleanup complete: Deleted {deleted_count} old files from {directory}")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error during cleanup of {directory}: {e}")
        return 0


def backup_file(filepath, backup_directory=None):
    """Create a backup copy of a file"""
    try:
        if not os.path.exists(filepath):
            print(f"❌ File not found for backup: {filepath}")
            return None
        
        # Default backup directory
        if backup_directory is None:
            backup_directory = os.path.join(os.path.dirname(filepath), 'backups')
        
        ensure_directory_exists(backup_directory)
        
        # Create backup filename with timestamp
        original_filename = os.path.basename(filepath)
        name, ext = os.path.splitext(original_filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{name}_backup_{timestamp}{ext}"
        backup_filepath = os.path.join(backup_directory, backup_filename)
        
        # Copy file
        import shutil
        shutil.copy2(filepath, backup_filepath)
        
        print(f"📋 Backup created: {backup_filepath}")
        return backup_filepath
        
    except Exception as e:
        print(f"❌ Error creating backup of {filepath}: {e}")
        return None


def calculate_directory_size(directory_path):
    """Calculate total size of all files in a directory"""
    try:
        total_size = 0
        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                    file_count += 1
                except OSError:
                    # Skip files that can't be accessed
                    continue
        
        size_mb = total_size / (1024 * 1024)
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(size_mb, 2),
            'file_count': file_count
        }
        
    except Exception as e:
        print(f"❌ Error calculating directory size for {directory_path}: {e}")
        return None