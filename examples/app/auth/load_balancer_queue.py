import zmq
import logging
from zmq.utils.garbage import gc


def start_load_balancer_server():
    try:
        context = zmq.Context()
        # context.set(zmq.MAX_SOCKETS, 32000)

        EXPOSE_PORT = "5558"
        gateway = context.socket(zmq.ROUTER)
        # gc.context = gateway
        gateway.bind(f"tcp://*:{EXPOSE_PORT}")
        logging.info(f"Starting load balancer server at {EXPOSE_PORT}")

        backend = context.socket(zmq.DEALER)
        backend.bind("ipc://stream")

        zmq.proxy(gateway, backend)

    except Exception as e:
        print(e)
        print("bringing down zmq device")
    finally:
        pass
        gateway.close()
        backend.close()
        context.term()
