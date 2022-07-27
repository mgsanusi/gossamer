from gevent import monkey
monkey.patch_all()

from flask import Flask, request
from app.classes import EphemeralLoginData
from multiprocessing import Value

from datetime import datetime
import zmq
import hashlib
import json

#####################################################
counter = Value("i", 0)
app = Flask(__name__)
context = zmq.Context()

socket = context.socket(zmq.PUSH)
socket.connect("tcp://127.0.0.1:5559")

# Sampling: Can be used to only log 1 out of k requests. Toggle using the boolean `sample`
k = 3
sample = False # Toggle this depending on whether you went sampling turned on or off
#####################################################

@app.route("/")
def hello():
    return "Hello world!"

@app.route("/login/", methods=["POST", "GET"])
def login():
    print("Request to login/ received")

    if sample:
        username = request.form["username"]
        hashed_username = hashlib.sha1(username.encode()).hexdigest()
        bitstring= "".join(format(ord(i), "b") for i in hashed_username)
        if bitstring[k*(-1):] != "0"*k:
            return "skipped"

    request_json = request.get_json()
    ts = datetime.utcfromtimestamp(int(request_json.get("timestamp")))

    with counter.get_lock():
        login_data = EphemeralLoginData(
            counter.value,
            request_json.get("username"),
            request_json.get("password"),
            request_json.get("remote_addr"),
            request_json.get("result"),
            json.dumps(request_json.get("request_headers")),
            ts)
        counter.value += 1

    # Now call store in the database accessor file
    print("Sending to heuristics worker to be processed..\n")
    try:
        socket.send_pyobj(login_data)
    except Exception as e:
        print(e)

    return "success"
