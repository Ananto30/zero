from typing import Callable
import zmq
import logging
import os

"""
If we want to replace the client-server patter with other implementation like Simple Pirate pattern,
implement the ZeroMQInterface class and replace the ZeroMQ with the new implementation instance.
"""


class ZeroMQInterface:
    def queue_device(
        self,
        worker_ipc: str,
        worker_port: int,
        host: str,
        port: int,
    ):
        """
        A queue_device maintains a queue to distribute the requests among the workers.

        Remember the queue device is blocking.

        Parameters
        ----------
        worker_ipc: str
            The address where all worker will connect.
            By default we use ipc for faster communication.
            But some os don't support ipc, in that case we use tcp and need the worker_port.
        worker_port: int
            It is used if ipc is not supported by os.
        host: str
            The host address where the device will listen from clients.
        port: int
            The port where the device will listen from clients.
        """
        raise NotImplementedError()

    def worker(
        self,
        worker_ipc: str,
        worker_port: int,
        worker_id: int,
        process_message: Callable,
    ):
        """
        A worker is a process that will handle the requests.

        Parameters
        ----------
        worker_ipc: str
            The address where all worker will connect.
            By default we use ipc for faster communication.
            But some os don't support ipc, in that case we use tcp and need the worker_port.
        worker_port: int
            It is used if ipc is not supported by os.
        worker_id: int
            The id of the worker.
        process_message: Callable
            The function that will process the message.
            It takes the rpc method name and msg in parameters as bytes and should return the reply in bytes.

            def process_message(rpc: bytes, msg: bytes) -> bytes:
                ...
        """
        raise NotImplementedError()


class ZeroMQPythonDevice(ZeroMQInterface):
    def queue_device(
        self,
        host: str,
        port: int,
        worker_ipc: str,
        worker_port: int,
    ):
        try:
            ctx = zmq.Context.instance()
            gateway = ctx.socket(zmq.ROUTER)
            gateway.bind(f"tcp://{host}:{port}")
            logging.info(f"Starting server at {host}:{port}")
            backend = ctx.socket(zmq.DEALER)

            if os.name == "posix":
                backend.bind(f"ipc://{worker_ipc}")
            else:
                backend.bind(f"tcp://127.0.0.1:{worker_port}")

            zmq.device(zmq.QUEUE, gateway, backend)

            gateway.close()
            backend.close()
            ctx.term()
        except Exception as e:
            logging.exception(e)
            logging.error("bringing down zmq device")

    def worker(
        self,
        worker_ipc: str,
        worker_port: int,
        worker_id: int,
        process_message: Callable,
    ):
        try:
            ctx = zmq.Context()
            socket = ctx.socket(zmq.DEALER)

            if os.name == "posix":
                socket.connect(f"ipc://{worker_ipc}")
            else:
                socket.connect(f"tcp://127.0.0.1:{worker_port}")

            logging.info(f"Starting worker: {worker_id}")

            while True:
                ident, rpc, msg = socket.recv_multipart()
                response = process_message(rpc, msg)
                socket.send_multipart([ident, response], zmq.DONTWAIT)

        except Exception as e:
            logging.exception(e)
        finally:
            socket.close()
            ctx.term()


# IMPORTANT: register the imlementation here
ZeroMQ = ZeroMQPythonDevice()
