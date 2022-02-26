import socket
import select
import struct 

DEFAULT_BLOCK_SIZE = 512
DEFAULT_WINDOW_SIZE = 1
MAX_WIN_SIZE = 100
MAX_BLOCK_SIZE = 65530

def get_op(packet):
    return struct.unpack('>h', packet[0:2])[0]

def parse_rrq(packet):
    blocks = packet[2:].split(b'\x00')
    print(packet)
    ret_block_size = DEFAULT_BLOCK_SIZE
    ret_windows_size = DEFAULT_WINDOW_SIZE
    for i in range(0, len(blocks) - 1):
        if (blocks[i] == b'blksize'):
            val = int(blocks[i + 1])
            if val >= 30 and val <= MAX_BLOCK_SIZE:
                ret_block_size = val
            else:
                print('abnormal block size, block_size =i ', val)
        if (blocks[i] == b'windowsize'):
            val = int(blocks[i + 1])
            if val >= 1 and val <= MAX_WIN_SIZE:
                ret_window_size = val
            else:
                print('abnormal window size, win_size =i ', val)
    return (blocks[0], blocks[1], ret_block_size, ret_window_size)

def get_block_num(data):
    return struct.unpack('>h', data[2:4])[0]

def data_request(block_num, data):
    request = struct.pack('>h', 3)
    request += struct.pack('>h', block_num)
    request += data + b'\x00'
    return request

def oack_request(block_size, window_size):
    request = struct.pack('>h', 6)
    request += b'windowsize' + b'\x00' + bytes(str(window_size), 'utf-8') + b'\x00' 
    request += b'blksize' + b'\x00' + bytes(str(block_size), 'utf-8') + b'\x00'
    return request

class Client:
    def __init__(self, sock, packet, addr):
        self.sock = sock
        self.addr = addr
        (self.filename, self.mode, self.block_size, self.window_size) = parse_rrq(packet)
        sock.sendto(oack_request(self.block_size, self.window_size), addr) #always?
        try:
            self.file = open(self.filename, "rb")
        finally:
            self.dead = True
            return
        self.last_processed = -1
        self.bricks = dict()        
        self.all_blocks = -2
        self.dead = False

    def get_sock(self):
        return self.sock
    def get_addr(self):
        return self.addr
    def is_dead(self):
        return self.dead        

    def conqueror_and_conqueror(self):
        if self.is_dead():
            return
        packet, addr = self.sock.recvfrom(256)
        print(packet, '  TYTYT ', get_op(packet))
        if get_op(packet) != 4:
            self.dead = True
            return
        block_num = get_block_num(packet)
        if block_num == self.all_blocks:
            self.dead = True
            return
        for i in range(block_num + 1, self.window_size + block_num + 1):
            if self.bricks.get(i) is None:
                self.bricks[i] = self.file.read(self.block_size)
            brick = self.bricks.get(i)
            self.sock.sendto(data_request(i, brick), self.addr)
            if len(brick) < self.block_size:
                self.all_blocks = i
                return

PORT = 1234
MAX_SIZE = 2048
HOST = ('', PORT)
clients = dict()
expired_time = dict()

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as main_sock:
    main_sock.bind(HOST)
    ep = select.epoll(1)
    ep.register(main_sock.fileno(), select.EPOLLIN)
    
    while True:
        for fileno, event in ep.poll(10):
            print(fileno, event)
            if fileno == main_sock.fileno() and event == select.EPOLLIN:
                packet, addr = main_sock.recvfrom(256)
                print(get_op(packet))
                if get_op(packet) != 1:
                    continue
                print('Finding a new bro!')
                client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                clients[client_sock.fileno()] = Client(client_sock, packet, addr)
                ep.register(client_sock.fileno(), select.EPOLLIN)
            elif fileno in clients and event == select.EPOLLIN:
                actual_client = clients[fileno]
                actual_client.conqueror_and_conqueror()
                if actual_client.is_dead():
                    ep.unregister(actual_client.get_sock().fileno())
                    clients.pop(actual_client.get_sock().fileno())                    
                    actual_client.get_sock().close()
                    print('We lost him, RIP dear ', actual_client.get_addr())

