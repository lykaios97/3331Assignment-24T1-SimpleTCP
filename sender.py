import sys
import os
import socket
import random
import collections
import time
import segment
import event_logger
from loss import roll_dice

BUF_SIZE = 1024

SEQ_NUM = 0
TYPE = 1
DATA = 2

DATA_TYPE = 0
ACK_TYPE = 1
SYN_TYPE = 2
FIN_TYPE = 3

STATE_CLOSED = -1
STAT_SYN_SENT = 1
STATE_EST = 2
STATE_CLOSING = 3
STATE_FIN_WAIT = 4

MSS = 1000

def create_next(content, offset, mss):
    seg = segment.create_segment(offset + start_seq, DATA_TYPE)
    if ((mss + offset) < len(content)):
        seg = segment.set_data(seg,content[offset:offset + mss])
    else:
        seg = segment.set_data(seg,content[offset:])
    return seg

# parse function below
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
    """Check file"""
    if mode == 'read' and (not os.path.isfile(file_path) or not os.access(file_path, os.R_OK)):
        sys.exit(f"File {file_path} does not exist or is not readable.")
    elif mode == 'write' and os.path.exists(file_path):
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
    """Check window size argument."""
    win_size = parse_positive_integer(win_size_str, "window size")
    if win_size < 1000 or win_size % 1000 != 0:
        sys.exit(f"Window size must be at least 1000 bytes and a multiple of 1000: {win_size}")
    return win_size

def parse_probability(prob_str, description="probability"):
    """Parse and validate that a value is a float between 0 and 1."""
    try:
        probability = float(prob_str)
        if not (0 <= probability <= 1):
            raise ValueError("Probability must be between 0 and 1.")
    except ValueError:
        sys.exit(f"Invalid {description}, must be a float between 0 and 1: {prob_str}")
    
    return probability

# 2 way handshake that have a max number of attempts to retransmitt the ack packet
def hand_shake(socket, receiver_port, rto):
    # Create SYN packet
    global start_seq
    start_seq = random.randint(0, 2**16 - 1)
    syn_packet = segment.create_segment(start_seq, type=SYN_TYPE)
    attempts = 0
    max_attempts = 10  # Maximum number of retransmissions set at 10 for debugging

    while attempts < max_attempts:
        # Send SYN packet
        socket.sendto(str(syn_packet), ('localhost', receiver_port))
        sender_state = STAT_SYN_SENT
        event_logger.log_event('snd', time.time(), 'SYN', segment.get_seq_no(syn_packet),0)
        print(f"SYN packet sent to port {receiver_port}. Attempt {attempts + 1}.")
        # Set timeout for receiving ACK
        socket.settimeout(rto / 1000)
        try:
            # Receive ACK
            response, addr = socket.recvfrom(BUF_SIZE)
            ack_packet = eval(response)
            # Check if received packet is an ACK
            if segment.is_type(ack_packet, ACK_TYPE):
                event_logger.log_event('rcv',time.time(),'ACK',segment.get_seq_no(syn_packet),0)
                print("Handshake successful. Connection established.")
                start_seq += 1
                socket.settimeout(None)  # Reset the timeout to default
                return True
            else:
                print("Received packet is not a valid ACK.")
                attempts += 1

        except socket.timeout:
            print("Timeout occurred. Resend")
            attempts += 1

    print("Handshake failed after maximum attempts.")
    return False

def read_file (file_path):
    fd = open(file_path, "r")
    content = fd.read()
    return content

def update_win (window, ack):
    for obj in window:
        if (obj['expected_ack'] == ack):
            obj['acked'] = True

def slide_win_base (window, base):
    for obj in window:
        if not obj["acked"]:
            new_base = obj['offset']
            return new_base
    return base

def transfer (s,receiver_port,content,MSS,window_size,rto,flp,rlp,seed):
    transfer_complete = False
    win_base = 0
    offset = 0
    window = []
    acks_receved = []
    # transfer is not completed for the whole file
    while not transfer_complete:
        # fill window
        while len(window) < window_size and offset < len(content):
            offset = win_base + (MSS * len(window))
            if (offset < len(content)):
                cont_len = len(content)
                expected_ack = offset + start_seq + cont_len
                new_seg = create_next(content,offset,MSS)
                window_obj = {'segment': new_seg,'offset': offset,'acked': False,'expected_ack': expected_ack}
                window.append(window_obj)
                # send it
                roll_dice(s,new_seg,time.time(),receiver_port,seed,flp)
        try:
            drop = (random.random() > rlp)
            response, addr = s.recvfrom(1024)
            seg = eval(response)
            print(f"segment:{seg}")
            if (segment.is_type(seg,ACK_TYPE)):
                ack_no = segment.get_seq_no(seg)
                event_logger.log_event('rcv',time.time(),'ACK',ack_no,0)
                if (ack_no - start_seq >= len(content)):
                    transfer_complete = True
                else:
                    update_win(window,ack_no)
                    win_base = slide_win_base(window,win_base)    
                    i = 0
                    while i < len(window):
                        if window[i]['offset'] < win_base:
                            del window[i]
                        else:
                            i += 1
        except socket.timeout:
            for obj in window:
                if not obj['acked']:
                    seg = obj['segment']
                    roll_dice(s,seg,time.time(),receiver_port,seed,flp)
                    print(f"resend {obj}")
        else:
            pass
def terminate (s, receiver_port, cont_len):
    fin_no = cont_len + start_seq + 1
    expected_fin_ack = fin_no + 1
    fin_seg = segment.create_segment(fin_no, type=FIN_TYPE)
    attempt = 0
    max_attempts = 10
    while attempt < max_attempts:
        socket.sendto(str(fin_seg), ('localhost', receiver_port))
        sender_state = STATE_CLOSING
        s.settimeout(rto / 1000)
        try:
            response, addr = s.recvfrom(BUF_SIZE)
            fin_ack = eval(response)
            if (segment.is_type(fin_ack, ACK_TYPE) and segment.get_seq_no(fin_ack) == expected_fin_ack):
                event_logger.log_event('rcv', time.time(), 'ACK', segment.get_seq_no(fin_ack), 0)
                print("Connection terminated successfully.")
                s.settimeout(None)
                return True
            else:
                print("Received packet is not a valid ACK.")
                attempts += 1
        except socket.timeout:
            print("Timeout occurred. Resend FIN.")
            attempts += 1
    print("Imma die ")
    return False
if __name__ == "__main__":
    global hand_shake_status
    hand_shake_status = False
    if len(sys.argv) != 8:
        print("Usage: python script.py <sender_port> <receiver_port> <file> <window_size> <rto> <flp> <rlp>")
        sys.exit(1)

    sender_port = parse_port(sys.argv[1])
    receiver_port = parse_port(sys.argv[2])
    file_path = parse_file_path(sys.argv[3], 'read')
    window_size = parse_window_size(sys.argv[4])
    rto = parse_positive_integer(sys.argv[5], "retransmission timeout (rto)")
    flp = parse_probability(sys.argv[6], "forward loss probability (flp)")
    rlp = parse_probability(sys.argv[7],)
    """print(f"{sender_port} {receiver_port} {file_path} {window_size} {rto} {flp} {rlp}")"""
    global sender_state
    seed = random.random()

    # start up the logger
    sender_start_time = time.time()
    event_logger.setup_logging()

    # create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(rto)
    sender_state = STATE_CLOSED
    hand_shake_status = hand_shake(s,receiver_port, rto)
    if hand_shake_status:
        sender_state = STATE_EST
    else :
        print("conneciton not established")
        sys.exit()
    content = read_file(file_path)
    transfer(s,receiver_port,content,MSS,window_size,rto,flp,rlp,seed)
    cont_len = len(content)
    termination_state = terminate(s,receiver_port,cont_len,seed,rlp)
    if termination_state:
        print("connection terminated")
        sender_state = STATE_CLOSED