import logging
import random

import zmq

from .controller import Controller

logging.basicConfig(format='%(asctime)s | %(process)d | %(module)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


port = 6666
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect(f"tcp://*:{port}")
logging.info(f"Starting order server at {port}")
server_id = random.randrange(1,10005)

while True:
    event = socket.recv()

    response = Controller.handle_request(event)

    socket.send(response)
