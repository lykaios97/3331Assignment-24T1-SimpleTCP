import sys
import os

# segment type base on spec
SYN = 0
ACK = 1
DATA = 2
FIN = 3

#states base on the spec
STATE_CLOSED = 0
STATE_SYN_SENT = 1
STATE_ESTABLISHED = 2
STATE_FIN_WAIT = 3

MSS = 1000
HEADER_FORMAT = '!HH'
LOG_FORMAT = "{event} {time:.2f} {type} {seq_no} {size}\n"

def parse_port(port_str, min_port=49152, max_port=65535):
    """Parse the port argument from the command-line."""
    try:
        port = int(port_str)
    except ValueError:
        sys.exit(f"Invalid port argument, must be numerical: {port_str}")
    
    if not (min_port <= port <= max_port):
        sys.exit(f"Port must be between {min_port} and {max_port}: {port}")
    
    return port

def parse_file_path(file_path, mode):
    """Check if the file is accessible in the specified mode."""
    if mode == 'write' and os.path.exists(file_path):
        print(f"Warning: File {file_path} exists and may be overwritten.")
    return file_path

def parse_positive_integer(value_str, description="value"):
    """Parse and validate that a command-line argument is a positive integer."""
    try:
        value = int(value_str)
        if value <= 0:
            raise ValueError("Value must be positive.")
    except ValueError:
        sys.exit(f"Invalid {description}, must be a positive integer: {value_str}")
    
    return value

def parse_window_size(win_size_str):
    """Parse and validate the window size argument."""
    win_size = parse_positive_integer(win_size_str, "window size")
    if win_size < 1000 or win_size % 1000 != 0:
        sys.exit(f"Window size must be at least 1000 bytes and a multiple of 1000: {win_size}")
    return win_size

def init_receiver():
    if len(sys.argv) != 5:
        print("Usage: python3 receiver.py <receiver_port> <sender_port> <txt_file_received> <max_win>")
        sys.exit(1)

    receiver_port = parse_port(sys.argv[1])
    sender_port = parse_port(sys.argv[2])
    txt_file_received = parse_file_path(sys.argv[3], 'write')
    max_win = parse_window_size(sys.argv[4])


if __name__ == "__main__":
    init_receiver()