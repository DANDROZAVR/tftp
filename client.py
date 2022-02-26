import socket
import struct
import time
import sys

PORT = 1234
HOSTNAME = 'localhost'
filename='a.txt'

arg_num = len(sys.argv) - 1
if arg_num != 3 and arg_num > 0:
    print('arg_num =', arg_num, '. Should be either 0 or 3')
    exit(0)
if arg_num > 0:
    PORT = int(sys.argv[1])
    HOSTNAME = sys.argv[2]
    filename = sys.argv[3]

mode = 'netascii'
block_size = 200
host = (HOSTNAME, PORT)
win_size = 5
MAX_BLOCK_SIZE = 65530
MAX_WIN_SIZE = 100

def send_rrq_request(sock, filename, mode):
    request = struct.pack('>h', 1)
    request += bytes(filename, 'utf-8') + b'\x00'    
    request += bytes(mode, 'utf-8') + b'\x00'
    request += b'windowsize' + b'\x00' + bytes(str(win_size), 'utf-8') + b'\x00' # change to struct?
    request += b'blksize' + b'\x00' + bytes(str(block_size), 'utf-8') + b'\x00' 
    sock.sendto(request, host)

def get_block_num(data):
    return struct.unpack('>h', data[2:4])

def parse_data(packet):
    block_num = struct.unpack('>h', packet[2:4])[0]
    data = packet[4:]
    return (block_num, data)

def parse_rrq(packet):
    blocks = packet[2:].split(b'\x00')
    filename = blocks[0]
    return (filename)

def parse_confirm(packet):
    blocks = packet[2:].split(b'\x00')
    ret_block_size = 0
    ret_window_size = 0
    print(packet)
    for i in range(0, len(blocks) - 1):
        if (blocks[i] == b'blksize'):
            val = int(blocks[i + 1])
            if val >= 30 and val <= MAX_BLOCK_SIZE:
                ret_block_size = val
            else:
                print('abnormal block size, block_size =i ', val)
                exit(1)
        if (blocks[i] == b'windowsize'):
            val = int(blocks[i + 1])
            if val >= 1 and val <= MAX_WIN_SIZE:
                ret_window_size = val
            else:
                print('abnormal window size, win_size =i ', val)
                exit(1)    
    return (ret_block_size, ret_window_size)

def send_ack(sock, block_num):
    packet = struct.pack('>h', 4)
    packet += struct.pack('>h', block_num)
    sock.sendto(packet, host)
    
def get_op(packet):
    return struct.unpack('>h', packet[0:2])[0]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
send_rrq_request(sock, filename, mode)

file = open(filename, 'wb')
actual_block = 1;
win_start = 1

while True:
    req_ans, new_addr = sock.recvfrom(5 + block_size) #less?
    host = new_addr
    print(req_ans)
    op = get_op(req_ans)
    if mode == 'netascii':
        if op == 3:
            (block_num, data) = parse_data(req_ans)        
            if (block_num != actual_block):
                send_ack(actual_block - 1)
                # should change win_start?
                continue                
            actual_block += 1
            file.write(data)
            if block_num == win_start + win_size - 1:
                win_start += win_size
                send_ack(sock, actual_block - 1)
            if len(data) < block_size:
                send_ack(sock, actual_block - 1)
                exit(0)
        elif op == 6:
            (block_size, win_size) = parse_confirm(req_ans)
            send_ack(sock, 0)
    else:
        print('unsupported mode')
        exit(0)
