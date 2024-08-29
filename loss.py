import random
import event_logger
import segment
import time

SEQ_NUM = 0
TYPE = 1
DATA = 2

# probability implementation for both flp and rlp
def roll_dice(socket, segment_to_send, curr_time, port, seed, probability):
    random.seed(seed)
    num = random.random()
    #send
    if (num > probability):
        socket.sendto(str(segment_to_send), ('localhost', port))
        event_logger.log_event('snd',time.time(),segment.get_segment_type(segment_to_send),segment.get_seq_no(segment_to_send),len(segment_to_send[DATA]))
    else:
        event_logger.log_event('drp',time.time(),segment.get_segment_type(segment_to_send),segment.get_seq_no(segment_to_send),len(segment_to_send[DATA]))
        

