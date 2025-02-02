# Echo client program
import socket
import pickle
import time
from threading import Event, Thread

SLEEP_TIME = 0.1
event = Event()
HOST = '127.0.0.1'    # The remote host
PORT = 8080             # The same port as used by the server

def packing(things: list):
    return '#'.join(things).encode()

def connect_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    return s

def register_name(name, mode, s):
    
    content = packing(['register', name, mode])
    s.sendall(content)
    time.sleep(SLEEP_TIME)
    data = s.recv(1024).decode('utf-8')
    return data == 'Connected'

def request_online_list(s):
    content = packing(['online_list'])
    s.sendall(content)
    online_list = s.recv(8192)
    
    return pickle.loads(online_list) 

def send_opponent(s, opponent):
    content = packing(['active_req', opponent])
    s.sendall(content)

def passive_recv_req(s):
    data = s.recv(8192).decode('utf-8')
    return data[4:] if data.startswith('req') else -1


def active_req_ok(s):
    data = s.recv(8192).decode('utf-8')
    return data == 'OK'

def passive_send_ok(s, opponent):
    content = packing(['passive_confirm', opponent])
    s.sendall(content)
    
def get_game_order(s, first_game, passive):
    game_cnt = 'first' if first_game else 'second'
    mode = 'passive' if passive else 'active'
    content = packing(['game_order', game_cnt, mode])
    s.sendall(content)
    data = s.recv(8159).decode('utf-8')
    print(data)
    if data == 'white' or data == 'black':
        return data
    else:
        return -1

def disconnect(s):
    s.sendall('disconnect'.encode())
    stop_sending_trash()
    
def sending_trash(s, event):
    while True:
        if event.is_set():
            break
        else:
            time.sleep(SLEEP_TIME)
            s.sendall('no_event'.encode())

def start_sending_trash(s):
    event.clear()
    Thread(target=sending_trash, args=(s, event)).start()
def stop_sending_trash():
    event.set()
    