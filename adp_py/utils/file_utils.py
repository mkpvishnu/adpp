"""
@ai-metadata {
    "domain": "utilities",
    "description": "File utility functions for ADP",
    "dependencies": []
}
"""

import os
import glob
from typing import List, Set, Optional, Iterator, Pattern
import re


def get_files_by_extension(directory: str, extensions: List[str], recursive: bool = True) -> List[str]:
    """
    Get all files with specified extensions in a directory.
    
    Args:
        directory: Directory to search
        extensions: List of file extensions to include (e.g. ['.py', '.js'])
        recursive: Whether to search recursively
    
    Returns:
        List of file paths
    """
    files = []
    
    if recursive:
        for ext in extensions:
            pattern = os.path.join(directory, f'**/*{ext}')
            files.extend(glob.glob(pattern, recursive=True))
    else:
        for ext in extensions:
            pattern = os.path.join(directory, f'*{ext}')
            files.extend(glob.glob(pattern))
    
    return sorted(files)


def find_files_by_pattern(directory: str, pattern: str, recursive: bool = True) -> List[str]:
    """
    Find files matching a glob pattern.
    
    Args:
        directory: Base directory to search
        pattern: Glob pattern to match (e.g. '*.py')
        recursive: Whether to search recursively
    
    Returns:
        List of matching file paths
    """
    full_pattern = os.path.join(directory, pattern)
    return sorted(glob.glob(full_pattern, recursive=recursive))


def filter_files_by_regex(files: List[str], pattern: str) -> List[str]:
    """
    Filter a list of files by a regex pattern.
    
    Args:
        files: List of file paths
        pattern: Regex pattern to match against the file path
    
    Returns:
        Filtered list of file paths
    """
    regex = re.compile(pattern)
    return [f for f in files if regex.search(f)]


def get_directories(path: str, recursive: bool = False) -> List[str]:
    """
    Get all directories in a path.
    
    Args:
        path: Path to search
        recursive: Whether to search recursively
    
    Returns:
        List of directory paths
    """
    if recursive:
        result = []
        for root, dirs, _ in os.walk(path):
            result.extend([os.path.join(root, d) for d in dirs])
        return sorted(result)
    else:
        return sorted([os.path.join(path, d) for d in os.listdir(path) 
                if os.path.isdir(os.path.join(path, d))])


def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is binary or text.
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if the file is binary, False if it's text
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # Try to read as text
            return False
    except UnicodeDecodeError:
        return True


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to ensure
    """
    os.makedirs(directory, exist_ok=True) 