import time

# Constants for log file names
LOG_FILE = "sender_log.txt"
# Setup log files by clearing existing contents or creating a new file
def setup_logging():
    global start_time
    start_time = time.time()
    with open(LOG_FILE, 'w') as f:
        f.write("")  # Clear existing contents or create a new file

# Log a packet event
def log_event(event_type, time_now, segment_type, seq_num, num_bytes):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{event_type} {time_elapse(time_now):.2f} {segment_type} {seq_num} {num_bytes}\n")

def time_elapse (time_now):
    elapsed = (time_now - start_time) * 1000
    return int(elapsed)

# Function to calculate and log statistics
def log_statistics():
    stats = {
        'total_data_sent': 0,
        'total_data_acked': 0,
        'data_segments_sent': 0,
        'retransmitted_segments': 0,
        'duplicate_acks_received': 0,
        'data_segments_dropped': 0,
        'ack_segments_dropped': 0
    }
    dropped_data = []
    received_acks = []

    # Read the log file and compute statistics
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) != 5:
            continue

        event_type, time, segment_type, seq_num, num_bytes = parts
        seq_num = int(seq_num)
        num_bytes = int(num_bytes)

        if segment_type == 'DATA':
            if event_type == 'snd':
                if seq_num in dropped_data:
                    stats['retransmitted_segments'] += 1
                stats['data_segments_sent'] += 1
                stats['total_data_sent'] += num_bytes
            elif event_type == 'drp':
                stats['data_segments_dropped'] += 1
                dropped_data.append(seq_num)
        elif segment_type == 'ACK':
            if event_type == 'rcv':
                stats['total_data_acked'] += num_bytes
                if seq_num in received_acks:
                    stats['duplicate_acks_received'] += 1
                received_acks.append(seq_num)
            elif event_type == 'drp':
                stats['ack_segments_dropped'] += 1

    # Log statistics at the end of the file
    with open(LOG_FILE, 'a') as f:
        f.write("\nStatistics:\n")
        f.write(f"Original data sent: {stats['total_data_sent']}\n")
        f.write(f"Original data acked: {stats['total_data_acked']}\n")
        f.write(f"Original segments sent: {stats['data_segments_sent']}\n")
        f.write(f"Retransmitted segments: {stats['retransmitted_segments']}\n")
        f.write(f"Dup acks received: {stats['duplicate_acks_received']}\n")
        f.write(f"Data segments dropped: {stats['data_segments_dropped']}\n")
        f.write(f"Ack segments dropped: {stats['ack_segments_dropped']}\n")
