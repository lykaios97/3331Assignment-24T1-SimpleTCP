TYPE = 0
SEQ_NUM = 1
DATA = 2

DATA_TYPE = 0
ACK_TYPE = 1
SYN_TYPE = 2
FIN_TYPE = 3

def create_segment(seq_num=0, type=None, data=''):
    """Create a new segment (empty)"""
    return [type, seq_num, data]

def set_segment_type(segment, type):
    segment[TYPE] = type
    return segment

def is_type(segment, type):
    """Check if the segment has the specified type."""
    return segment[TYPE] == type

def set_data(segment, content):
    segment[DATA] = content
    return segment

def get_data(segment):
    return segment[DATA]

def set_seq_no(segment, seq_no):
    segment[SEQ_NUM] = seq_no
    return segment

def get_seq_no(segment):
    return segment[SEQ_NUM]

def get_segment_type(segment):
    """Get the type of the segment."""
    type = segment[TYPE]
    if type == DATA_TYPE:
        return 'DATA'
    elif type == ACK_TYPE:
        return 'ACK'
    elif type == SYN_TYPE:
        return 'SYN'
    elif type == FIN_TYPE:
        return 'FIN'
    return 'UNKNOWN'
