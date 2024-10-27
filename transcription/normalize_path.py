import os

def normalize_path(path):
    # Normalize slashes according to the operating system
    path = os.path.normpath(path)
    # Add long path prefix for Windows if needed
    if os.name == 'nt' and not path.startswith('\\\\?\\') and len(path) > 260:
        return '\\\\?\\' + os.path.abspath(path)
    return path