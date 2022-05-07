import json
import socket
import traceback
import time
import threading
import random

leader = ""
port = 5555
is_leader_set = False


# Get leader information
def leader_info(skt, nodes):
    request(skt, 'LEADER_INFO', nodes)

# Convert ALL nodes to follower state


def convert_all_to_follower(skt, nodes):
    request(skt, 'CONVERT_FOLLOWER', nodes)

# Convert a leader node to the follower state
def convert_leader_to_follower(skt, nodes):
    leader_info(skt, nodes)
    global is_leader_set
    while(not is_leader_set):
        continue
    is_leader_set = False
    request(skt, 'CONVERT_FOLLOWER', [leader])

# Shutdown any particular node
def shutdown_node(skt, nodes):
    shutdown_node = random.choice(nodes)
    request(skt, 'SHUTDOWN', [shutdown_node])


# Shutdown the leader node
def shutdown_leader(skt, nodes):
    leader_info(skt, nodes)
    global is_leader_set
    while(not is_leader_set):
        continue
    is_leader_set = False
    shutdown_node = leader
    request(skt, 'SHUTDOWN', [shutdown_node])

# Convert a node which has been shutdown
def convert_shutdown_node_to_follower(skt, nodes):
    shutdown_node = random.choice(nodes)
    request(skt, 'SHUTDOWN', [shutdown_node])
    time.sleep(2)
    request(skt, 'CONVERT_FOLLOWER', [shutdown_node])

# Timeout any particular node
def timeout_node(skt, nodes):
    timeout_node = random.choice(nodes)
    request(skt, 'TIMEOUT', [timeout_node])

# Timeout leader node
def timeout_leader(skt, nodes):
    leader_info(skt, nodes)
    global is_leader_set
    while(not is_leader_set):
        continue
    is_leader_set = False
    timeout_node = leader
    request(skt, 'TIMEOUT', [timeout_node])


def test_log_replication_shutdown_follower(skt, nodes):
    shutdown_node = random.choice(nodes)
    testCases[9](skt, nodes, "k1", "Value1")
    time.sleep(3)
    testCases[12](skt, nodes)
    request(skt, 'SHUTDOWN', [shutdown_node])
    time.sleep(3)
    testCases[9](skt, nodes, "k2", "Value2")
    time.sleep(3)
    testCases[12](skt, nodes)
    request(skt, 'CONVERT_FOLLOWER', [shutdown_node])
    time.sleep(5)
    testCases[9](skt, nodes, "k3", "Value3")
    time.sleep(5)
    testCases[12](skt, nodes)
    
def test_log_replication_shutdown_leader(skt, nodes):
    testCases[1](skt, nodes)
    time.sleep(5)
    testCases[9](skt, nodes, "k1", "Value1")
    time.sleep(3)
    temp_leader = leader
    request(skt, 'SHUTDOWN', [temp_leader])
    time.sleep(3)
    testCases[9](skt, nodes, "k2", "Value2")
    time.sleep(3)
    request(skt, 'CONVERT_FOLLOWER', [temp_leader])
    time.sleep(5)
    testCases[9](skt, nodes, "k3", "Value3")

def get_follower_log(skt, nodes):
    leader_info(skt, nodes)
    global is_leader_set
    while(not is_leader_set):
        continue
    is_leader_set = False
    for node in nodes:
        if node != leader:
            msg = {
                "sender_name": sender,
                "request": 'RETRIEVE_FOLLOWER_LOG',
            }
            msg_bytes = json.dumps(msg).encode()
            skt.sendto(msg_bytes, (node, port))  

def send_multiple_requests(skt, nodes):
    testCases[9](skt, nodes, "k1", "Value1")
    time.sleep(3)
    testCases[9](skt, nodes, "k2", "Value2")
    time.sleep(3)
    testCases[9](skt, nodes, "k3", "Value3")
    time.sleep(3)
    testCases[12](skt, nodes)

# Store new key, value
def store(skt, nodes, store_key, store_value):
    request(skt, "STORE", nodes, key=store_key, value=store_value)


# retrieve Commited logs
def retrieve(skt, nodes):
    request(skt, "RETRIEVE", nodes, key="", value="")
    
    
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


# Listener
def listener(skt):
    while True:
        msg, addr = skt.recvfrom(1024)
        decoded_msg = json.loads(msg.decode('utf-8'))
        print(f"Message Received : {decoded_msg} From : {addr}")

        if decoded_msg['request'] == 'LEADER_INFO':
            global leader
            leader = decoded_msg['value']
            global is_leader_set
            is_leader_set = True

        if decoded_msg['request'] == 'RETRIEVE_FOLLOWER_INDEX':
            print("Follower's Log Status ", decoded_msg['logs'])

# Send controller requests
def request(skt, request_type, nodes, key="", value=""):
    msg_bytes = create_msg('CONTROLLER', request_type, key, value)
    print(f"Request Created : {msg_bytes}")

    try:
        for target in nodes:
            skt.sendto(msg_bytes, (target, port))
    except:
        print(f"ERROR WHILE SENDING REQUEST ACROSS : {traceback.format_exc()}")


if __name__ == "__main__":
    time.sleep(5)
    sender = "Controller"
    nodes = ["Node1", "Node2", "Node3"]

    skt = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    skt.bind((sender, port))

    threading.Thread(target=listener, args=[skt]).start()
    run_test_case = True

    testCases = {
        1:  leader_info,
        2:  convert_all_to_follower,
        3:  convert_leader_to_follower,
        4:  shutdown_node,
        5:  shutdown_leader,
        6:  convert_shutdown_node_to_follower,
        7:  timeout_node,
        8:  timeout_leader,
        9:  store,
        10: retrieve,
        11: test_log_replication_shutdown_follower,
        12: get_follower_log, 
        13: send_multiple_requests,
        14: test_log_replication_shutdown_leader
    }

    # Run any single case
    time.sleep(2)
    testCases[11](skt, nodes)
