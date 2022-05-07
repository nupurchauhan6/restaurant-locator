import os

from setuptools import Command
from flask import Flask, render_template, request
from models import Restaurant
from __init__ import db, create_app
import requests
import uuid

import json
import socket
from tkinter.tix import Tree
import traceback
import threading
import time

app = create_app()
port=''
IS_LEADER = os.environ['IS_LEADER']
SENDER_PORT = int(os.environ['SENDER_PORT'])
CONTAINER = os.environ['CONTAINER']

leader = ""

commited = False
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

# Send controller requests
def request_msg(skt, request_type, nodes, key="", value=""):
    msg_bytes = create_msg(sender, request_type, key, value)
    print(f"Request Created : {msg_bytes}")

    try:
        for target in nodes:
            skt.sendto(msg_bytes, (target, 5555))
    except:
        print(f"ERROR WHILE SENDING REQUEST ACROSS : {traceback.format_exc()}")



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def get():
    if request.method == 'POST':
        result = []
        pincode = request.form.get('pincode')
        rows = Restaurant.query.filter_by(pincode=pincode).all()
        for row in rows:
            result.append({
                'name': row.name,
                'address': row.address,
                'pincode': row.pincode,
                'number': row.number,
            })
        return render_template('index.html', result=result)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        number = request.form.get('number')
        data = {
            "name": name,
            "address": address,
            "pincode": pincode,
            "number": number
        }
        uid = uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e0f}')
        print("reached here1?")
        

        
    
    if IS_LEADER == "True":
        store(str(uid), data)
        global commited
        while not commited:
            continue

        requests.post('http://rl_server2:5002/add',
                                    data=data)
        requests.post('http://rl_server3:5003/add',
                                  data=data)    
    
    # if commited:
    db.session.add(
        Restaurant(name=name,
                address=address,
                pincode=pincode,
                number=number))
    db.session.commit()

    return render_template('index.html')


# Listen for leader information
def listener(skt):
    while True:
        msg, addr = skt.recvfrom(1024)
        decoded_msg = json.loads(msg.decode('utf-8'))
        print(f"Message Received : {decoded_msg} From : {addr}")
        if decoded_msg['request'] == 'COMMITED_SUCCESSFULLY':
            if decoded_msg['success'] == True:
                print("########DDDDDD######")
                global commited
                commited = True



skt = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM )
skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
skt.bind((CONTAINER, SENDER_PORT))

threading.Thread(target=listener, args=[skt]).start()

# Store new key, value to Log
def store(store_key, store_value):
    request_msg(skt, "STORE", nodes, key=store_key, value=store_value)
    return


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT'))