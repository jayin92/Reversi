import socket
import threading
import pickle
import time

HOST = ''
PORT = 8080
MSG_SIZE = 8192
TIMEOUT = 100

client_dict = {} # key: name, value: (socket, addr)
passive_list = [] # List of clients who are waiting for opponent
match_list = [] # Use tuple to represent a match

def handle_match(client1, client2, client1_name, client2_name, first_macth):
    if first_macth:
        first, second = client1, client2
    else:
        first, second = client2, client1

    first.sendall("black".encode('utf-8'))
    second.sendall("white".encode('utf-8'))
    while True:
        # Receive move from first player
        try:
            move = first.recv(MSG_SIZE).decode('utf-8')
        except TimeoutError:
            print(f'{client1_name} timeout')
            return False
        if move == 'END':
            break
        second.sendall(move.encode('utf-8'))
        # Receive move from second player
        try:
            move = second.recv(MSG_SIZE).decode('utf-8')
        except TimeoutError:
            print(f'{client2_name} timeout')
            return False
        
        if move == 'END':
            break
        first.sendall(move.encode('utf-8'))
    
    return True



def handle_client(client_conn, client_addr):

    # Setup user
    global client_dict, match_list
    client_name = client_conn.recv(MSG_SIZE).decode('utf-8')

    if client_name in client_dict:
        client_conn.sendall('Name already exists'.encode('utf-8'))
        client_conn.close()
        return
    
    client_dict[client_name] = (client_conn, client_addr)
    mode = client_conn.recv(MSG_SIZE).decode('utf-8')
    print(f'Client {client_name} connected')

    if mode == "passive":
        client_conn.sendall('Connected'.encode('utf-8'))
        passive_list.append(client_name)
        threading.Thread(target=sending_trash, args=[client_conn]).start()    
        time.sleep(1000000)
        
    elif mode == "active":
        client_conn.sendall('Connected'.encode('utf-8'))
        # Refresh online list
        while True:
            fg = client_conn.recv(MSG_SIZE).decode('utf-8')
            print(fg)
            if fg == 'online_list':
                client_conn.sendall(pickle.dumps(passive_list))
            else:
                break
        # Recieve opponent
        while True:
            opponent = client_conn.recv(MSG_SIZE).decode('utf-8')
            print('recieving opponent')
            if opponent not in passive_list:
                client_conn.sendall('This user not available'.encode('utf-8'))
                client_conn.sendall(pickle.dumps(passive_list))
            else:
                print(f'{client_name} wants to play with {opponent}')
                client_conn.sendall('Waiting for opponent'.encode('utf-8'))
                threading.Thread(target=sending_trash, args=[client_conn]).start()
                while True:
                    client_dict[opponent][0].sendall(f'req {client_name}'.encode('utf-8'))
                    try:
                        confirm = client_dict[opponent][0].recv(MSG_SIZE).decode('utf-8')
                    except:
                        continue
                    if confirm == 'OK':
                        break
                client_conn.sendall('OK'.encode())
                passive_list.remove(opponent)
                match_list.append((client_name, opponent))
                print(f'Match between {client_name} and {opponent} started')
                oppo_conn = client_dict[opponent][0]
                client_conn.settimeout(TIMEOUT)
                oppo_conn.settimeout(TIMEOUT)
                print(f"Black: {client_name}, White: {opponent}")
                exit_code = handle_match(client_conn, oppo_conn, client_name, opponent, True)
                if not exit_code:
                    print(f"Timeout error")
                    return
                client_conn.settimeout(None)
                oppo_conn.settimeout(None)
                client_conn.sendall('END'.encode('utf-8'))
                oppo_conn.sendall('END'.encode('utf-8'))
                client_res = client_conn.recv(MSG_SIZE).decode('utf-8') # Return "<black> <white>"
                oppo_res = oppo_conn.recv(MSG_SIZE).decode('utf-8')
                if client_res != oppo_res:
                    print('Error')
                    return
                else:
                    first_res = client_res.split(' ')
                    print(f'Result: Black: {first_res[0]}, White: {first_res[1]}')
                print(f"Black: {opponent}, White: {client_name}")
                client_conn.settimeout(TIMEOUT)
                oppo_conn.settimeout(TIMEOUT)
                exit_code = handle_match(client_conn, oppo_conn, client_name, opponent, True)
                if not exit_code:
                    print(f"Timeout error")
                    return
                client_conn.settimeout(None)
                oppo_conn.settimeout(None)
                client_conn.sendall('END'.encode('utf-8'))
                oppo_conn.sendall('END'.encode('utf-8'))
                client_res = client_conn.recv(MSG_SIZE).decode('utf-8') # Return "<black> <white>"
                oppo_res = oppo_conn.recv(MSG_SIZE).decode('utf-8')
                if client_res != oppo_res:
                    print('Error')
                    return
                else:
                    second_res = client_res.split(' ')
                    print(f'Result: Black: {second_res[0]}, White: {second_res[1]}')
                client_score = int(first_res[0]) + int(second_res[1])
                oppo_score = int(first_res[1]) + int(second_res[0])
                print(f"{client_name} has {client_score} points")
                print(f"{opponent} has {oppo_score} points")
                if client_score > oppo_score:
                    print(f"{client_name} won")
                elif client_score < oppo_score:
                    print(f"{opponent} won")
                else:
                    print("Draw")
                print(f'Match between {client_name} and {opponent} ended')
                break
    else:
        client_conn.sendall('Invalid mode'.encode('utf-8'))
        client_conn.close()
        return

    # Start a match

def sending_trash(conn):
    while True:
        conn.send(' '.encode())
        time.sleep(1)

def handle_disconnect(conn, addr):
    while True:
        try:
            data = conn.recv(8192).decode('utf-8')
        except:
            continue
        if 'disconnect' in data:
            print(f'{addr} disconnected')
            

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    # s.setblocking(False)
    s.listen(40) # Up to 40 clients
    print("Reversi server is running...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
        