from datetime import datetime

COLORS = {
    'green': '\033[92m',
    'yellow': '\033[93m',
    'red': '\033[91m',
    'reset': '\033[0m',
}

def log(message: str, color: str = 'reset') -> None:
    """Log a message with a timestamp and optional color."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    color_code = COLORS.get(color, '')
    reset = COLORS['reset']
    print(f"{color_code}[{timestamp}]{reset} {message}")
