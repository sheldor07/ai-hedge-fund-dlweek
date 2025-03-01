#!/usr/bin/env python3
import os
import re
import sys

def remove_comments_from_file(file_path):
    """Remove Python comments from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove docstrings (triple quotes)
    content = re.sub(r'"""[\s\S]*?"""', '', content)
    content = re.sub(r"'''[\s\S]*?'''", '', content)
    
    # Remove single line comments
    content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    
    # Clean up extra blank lines
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Removed comments from {file_path}")

def process_directory(directory):
    """Process all Python files in a directory and its subdirectories."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                remove_comments_from_file(file_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remove_comments.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)
    
    process_directory(directory)
    print(f"Completed removing comments from all Python files in {directory}")
