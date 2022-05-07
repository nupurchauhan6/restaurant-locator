import json
import socket
from tkinter.tix import Tree
import traceback
import threading


leader = ""
port = 5555
com = False
sender = "rl_server1"
nodes = ["Node1", "Node2", "Node3"]

# Create a message request
def create_msg(sender, request_type, key="", value=""):
    msg = {
        "sender_name": sender,
        "request": request_type,
        "term": None,
        "key": key,
        "value": value
    }
    msg_bytes = json.dumps(msg).encode()
    return msg_bytes


# Listen for leader information
def listener(skt):
    while True:
        msg, addr = skt.recvfrom(1024)
        decoded_msg = json.loads(msg.decode('utf-8'))
        print(f"Message Received : {decoded_msg} From : {addr}")
        if decoded_msg['request'] == 'COMMITED_SUCCESSFULLY':
            if decoded_msg['success'] == True:
                print("########DDDDDD######")
                global com 
                com = True
                # return decoded_msg['success']



# Send controller requests
def request(skt, request_type, nodes, key="", value=""):
    msg_bytes = create_msg(sender, request_type, key, value)
    print(f"Request Created : {msg_bytes}")

    try:
        for target in nodes:
            skt.sendto(msg_bytes, (target, port))
    except:
        print(f"ERROR WHILE SENDING REQUEST ACROSS : {traceback.format_exc()}")


skt = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM )
skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
skt.bind((sender, port))

threading.Thread(target=listener, args=[skt]).start()


# Store new key, value to Log
def store(store_key, store_value):
    request(skt, "STORE", nodes, key=store_key, value=store_value)
