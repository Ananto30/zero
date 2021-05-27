import gc
import logging
import time
from multiprocessing import Process, cpu_count
# from multiprocessing.pool import ThreadPool
from threading import Thread

import zmq
from zmq.devices import ProcessDevice, ThreadDevice

from .controller import Controller
from .load_balancer_queue import start_load_balancer_server

logging.basicConfig(format='%(asctime)s | %(threadName)s | %(process)d | %(module)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def start_broker():
    EXPOSE_PORT = "5558"
    pd = ThreadDevice(zmq.QUEUE, zmq.ROUTER, zmq.DEALER)
    pd.bind_in(f"tcp://*:{EXPOSE_PORT}")
    pd.bind_out("ipc://stream")
    pd.start()

def process_request(socket):
    while True:
        event = socket.recv()
        response = Controller.handle_request(event)
        socket.send(response)

        del event
        del response
        gc.collect()


def start_server(server_id):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    # socket = context.socket(zmq.DEALER)
    socket.connect("ipc://stream")
    logging.info(f"Starting order server id: {server_id}")
    process_request(socket)


if __name__ == "__main__":
    # Process(target=start_load_balancer_server).start()
    start_broker()
    time.sleep(.5)
    cores = cpu_count()
    for i in range(cores-1):
        Process(target=start_server, args=(i,)).start()
