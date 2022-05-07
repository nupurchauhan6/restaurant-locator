import socket
import json
import os
import time
import threading
import math
from raft import RaftNode
from constants import *
from termcolor import colored

# Create messenge request for request vote RPC
def create_msg_request_vote(sender, request, currentTerm, key="", value="", lastLogIndex=0, lastLogTerm=0):
    msg = {
        "sender_name": sender,
        "request": request,
        "term": currentTerm,
        "key": key,
        "value": value,
        "candidateId": sender,
        "lastLogIndex": lastLogIndex,
        "lastLogTerm": lastLogTerm
    }
    msg_bytes = json.dumps(msg).encode()
    return msg_bytes

# Create messenge request for append entry RPC
def create_msg_append_entry(sender, request, currentTerm, key="", value="", entries=[], prevLogIndex=0, prevLogTerm=0, commitIndex=0):
    msg = {
        "sender_name": sender,
        "request": request,
        "term": currentTerm,
        "key": key,
        "value": value,
        "leaderId": sender,
        "prevLogIndex": prevLogIndex,
        "prevLogTerm": prevLogTerm,
        "commitIndex": commitIndex,
        "entries": entries
    }
    msg_bytes = json.dumps(msg).encode()
    return msg_bytes

def create_msg_append_reply(sender, request, matchIndex, success=False, committed = False):
    msg = {
        "sender_name": sender,
        "request": request,
        "success": success,
        "matchIndex": matchIndex,
        "committed": committed
    }
    msg_bytes = json.dumps(msg).encode()
    return msg_bytes

# Create message request
def create_msg(sender, request, currentTerm, key="", value=""):
    msg = {
        "sender_name": sender,
        "request": request,
        "term": currentTerm,
        "key": key,
        "value": value
    }
    msg_bytes = json.dumps(msg).encode()
    return msg_bytes

# Receive vote requests from all nodes and cast a vote
def vote_request(skt, node: RaftNode, self_node, target, term, lastLogTerm, lastLogIndex):
    if node.currentTerm < term:
        node.currentTerm = term
        node.state = FOLLOWER
        node.votedFor = None
    
    safetyCheck = (node.getLogTerm() > lastLogTerm) or (node.getLogTerm() == lastLogTerm) and (node.getLogIndex() > lastLogIndex)
    if (node.votedFor == None) and (not safetyCheck):
        node.startTime = time.perf_counter()
        node.electionTimeout = node.getElectionTimeout()
        node.votedFor = target
        msg_bytes = create_msg(self_node, VOTE_ACK, node.currentTerm)
        skt.sendto(msg_bytes, (target, 5555))

# Check for majority of votes and convert itself to a Leader
def vote_ack(node: RaftNode, nodes, self_node):
    node.voteCount += 1
    if node.voteCount >= math.ceil((len(nodes)+1)/2.0):
        node.heartbeatTimeout = node.getHeartbeatTimeout()
        node.startTime = time.perf_counter()
        node.state = LEADER
        node.currentLeader = self_node
        
        # initialize nextIndex[] and matchIndex[] for each node
        node.nextIndex = []
        node.matchIndex = []
        for n in nodes:
            node.nextIndex.append(node.getLogIndex()+1)
            node.matchIndex.append(0)
        
# Receive heartbeats from leader node and reset election timeout
def append_rpc(node: RaftNode, term, leader, prevLogIndex, prevLogTerm, entries, leaderCommit):
    
    committed = False
    success = False
    matchIndex = 0
    if term < node.currentTerm:
        return (success, committed, matchIndex)
    elif node.state == CANDIDATE and term >= node.currentTerm:
        node.currentTerm = term
        node.state = FOLLOWER
        node.votedFor = None

    node.startTime = time.perf_counter()
    node.electionTimeout = node.getElectionTimeout()
    node.currentLeader = leader
    
    if len(entries) == 0:
        if node.commitIndex < leaderCommit:
            node.commitIndex = min(leaderCommit, prevLogIndex)
        success = True
        return (success, committed, matchIndex)
    
    if prevLogIndex < len(node.log):   
        if len(node.log) == 0:
            logTerm = 0
        else:
            entry = node.log[prevLogIndex]
            logTerm = entry["term"]

        if logTerm == prevLogTerm:
            node.log = node.log[:(prevLogIndex+1)] + entries
            success = True
            committed = True
            matchIndex = prevLogIndex + 1
            print("Follower's Log Status.....", node.log)
            return (success, committed, matchIndex)


    return (success, committed, matchIndex)


def append_reply(skt, node: RaftNode, nodes, self_node, sender, success, committed, matchIndex):
    sender_index = nodes.index(sender)
    self_index = nodes.index(self_node)
    if success == True:
        node.nextIndex[self_index] = node.getLogIndex()+1
        node.nextIndex[sender_index] = node.getLogIndex()+1
        if committed:
            node.matchIndex[sender_index] = matchIndex
            N  = max(set(node.matchIndex), key = node.matchIndex.count)
            if N > node.commitIndex:
                node.commitIndex = N
                msg_bytes = create_msg_append_reply(self_node, COMMITED_SUCCESSFULLY, success=True, committed = False, matchIndex = 0)
                skt.sendto(msg_bytes, ('rl_server1', 5556))
    elif success == False:
        node.nextIndex[self_index] -= 1
        node.nextIndex[sender_index] -= 1
            
# Convert a node to follower state
def convert_follower(node: RaftNode):
    node.state = FOLLOWER
    node.votedFor = None
    node.voteCount = 0
    node.shutdown = False
    node.startTime = time.perf_counter()
    node.electionTimeout = node.getElectionTimeout()

# Timeout a node immediately
def timeout(node: RaftNode):
    node.state = FOLLOWER
    node.startTime = time.perf_counter()
    node.electionTimeout = 0

# Send leader information to the controller
def leader_info(skt, node: RaftNode, self_node):
    msg_bytes = create_msg(
        self_node, LEADER_INFO, node.currentTerm, LEADER, node.currentLeader)
    skt.sendto(msg_bytes, ('rl_server1', 5555))

def is_leader(node: RaftNode):
    return node.state == LEADER

# Listen for incoming requests
def listener(skt, node: RaftNode, nodes, self_node):
    while True:
        msg, addr = skt.recvfrom(1024)
        decoded_msg = json.loads(msg.decode('utf-8'))

        if not node.shutdown or decoded_msg['request'] == CONVERT_FOLLOWER:
            print(f"Message Received : {decoded_msg} From : {addr}")

            if decoded_msg['request'] == VOTE_REQUEST:
                vote_request(
                    skt, node, self_node, decoded_msg['sender_name'], decoded_msg['term'], decoded_msg['lastLogTerm'], decoded_msg['lastLogIndex'])

            elif decoded_msg['request'] == VOTE_ACK:
                vote_ack(node, nodes, self_node)

            elif decoded_msg['request'] == APPEND_RPC:
                success, committed, matchIndex = append_rpc(node, decoded_msg['term'], decoded_msg['sender_name'], decoded_msg['prevLogIndex'],
                                  decoded_msg['prevLogTerm'], decoded_msg['entries'], decoded_msg['commitIndex'])
                
                msg_bytes = create_msg_append_reply(self_node, APPEND_REPLY, success=success, committed = committed, matchIndex = matchIndex)
                skt.sendto(msg_bytes, (decoded_msg['sender_name'], 5555))

            elif decoded_msg['request'] == CONVERT_FOLLOWER:
                print(colored('          ************************   Converting ' + self_node +
                      ' To Follower   ************************', 'yellow', attrs=['bold']))
                convert_follower(node)

            elif decoded_msg['request'] == TIMEOUT:
                print(colored('          ************************   Timing Out ' +
                      self_node + '   ************************', 'red', attrs=['bold']))
                timeout(node)

            elif decoded_msg['request'] == SHUTDOWN:
                print(colored('          ************************   Shutting Down ' +
                      self_node + '   ************************', 'red', attrs=['bold']))
                node.shutdown = True

            elif decoded_msg['request'] == LEADER_INFO:
                leader_info(skt, node, self_node)
                
            elif decoded_msg['request'] == STORE:
                if is_leader(node):
                    new_entry = {
                        'term': node.currentTerm,
                        'key': decoded_msg['key'],
                        'value': decoded_msg['value']
                    }
                    node.log.append(new_entry)
                else:
                    leader_info(skt, node, self_node)

            elif decoded_msg['request'] == RETRIEVE:
                if is_leader(node):
                    msg_bytes = create_msg(
                        decoded_msg['sender_name'], RETRIEVE, node.currentTerm, COMMITED_LOGS, node.log)
                    skt.sendto(msg_bytes, (decoded_msg['sender_name'], 5555))
                else:
                    leader_info(skt, node, self_node)

            elif decoded_msg['request'] == APPEND_REPLY:
                append_reply(
                    skt, node, nodes, self_node, decoded_msg['sender_name'], decoded_msg['success'], decoded_msg['committed'], decoded_msg['matchIndex'])
                
            elif decoded_msg['request'] == RETRIEVE_FOLLOWER_LOG:
                msg = {
                    "sender_name": sender,
                    "request": RETRIEVE_FOLLOWER_LOG,
                    "logs": node.log,
                    "commitIndex": node.commitIndex
                }
                msg_bytes = json.dumps(msg).encode()
                skt.sendto(msg_bytes, (decoded_msg['sender_name'], 5555))

# Sends RPCs
def messenger(skt, node: RaftNode, sender, targets):
    while(True):
        if not node.shutdown:
            if node.state == LEADER:
                if (node.startTime + node.heartbeatTimeout) < time.perf_counter():
                    node.heartbeatTimeout = node.getHeartbeatTimeout()
                    node.startTime = time.perf_counter()

                    for target in targets:
                        i = targets.index(target)
                        prevLogIndex = node.nextIndex[i]-1
                        if prevLogIndex == -1:
                            prevLogTerm = 0
                        else:
                            prevLogTerm = node.log[prevLogIndex]["term"]
                        if len(node.log) == 0:
                            entries = []
                        else:
                            entries = node.log[node.nextIndex[i]:node.nextIndex[i] + 1]
                        
                        msg_bytes = create_msg_append_entry(
                                sender, APPEND_RPC, node.currentTerm, entries=entries, prevLogTerm=prevLogTerm, prevLogIndex=prevLogIndex, commitIndex = node.commitIndex)
                        skt.sendto(msg_bytes, (target, 5555))

            if node.state == FOLLOWER:
                if (node.startTime + node.electionTimeout) < time.perf_counter():
                    print(colored(
                        '          ************************   Starting Elections  ************************', 'green', attrs=['bold']))
                    node.state = CANDIDATE
                    node.currentTerm += 1
                    node.votedFor = self_node
                    node.voteCount = 1
                    
                    lastLogIndex = node.getLogIndex()
                    lastLogTerm = node.getLogTerm()

                    for target in targets:
                        msg_bytes = create_msg_request_vote(
                            sender, VOTE_REQUEST, node.currentTerm, lastLogIndex = lastLogIndex, lastLogTerm = lastLogTerm)
                        skt.sendto(msg_bytes, (target, 5555))


if __name__ == "__main__":

    self_node = os.getenv('NODE_NAME')
    sender = self_node
    nodes = ["Node1", "Node2", "Node3", "Node4", "Node5"]
    targets = ["Node1", "Node2", "Node3", "Node4", "Node5"]
    targets.remove(self_node)
    node = RaftNode()

    UDP_Socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDP_Socket.bind((sender, 5555))

    threading.Thread(target=listener, args=[
                     UDP_Socket, node, nodes, self_node]).start()

    threading.Thread(target=messenger, args=[
        UDP_Socket, node, sender, targets]).start()