import logging

import msgpack

import zmq
import zmq.asyncio


class ZeroClient:
    def __init__(
        self,
        host: str,
        port: int,
        use_async: bool = True,
        serializer: str = "msgpack",
        default_timeout: int = 2000,
    ):
        """
        ZeroClient provides the client interface for calling the ZeroServer.

        @param host:
        Host of the ZeroServer.

        @param port:
        Port of the ZeroServer.

        @param use_async:
        For using async/await Python. The client calls will be async.
        True by default.
        Please use the `call_async` method to use the async interface.

        @param serializer:
        Serializer is used to convert the msg to bytes and vice-versa.
        Only `msgpack` is supported for now.

        @param default_timeout:
        Default timeout for each call. In milliseconds.
        """
        self._host = host
        self._port = port
        self._default_timeout = default_timeout
        if use_async:
            self._init_async_socket()
        else:
            self._init_socket()
        self._serializer = serializer

        # removed quickle as it is kind of broken for python objects, why? I dont know
        if serializer not in ["msgpack"]:
            raise Exception("serializer not supported")
        self._init_serializer()

    def _init_serializer(self):
        # msgpack is the default serializer
        if self._serializer == "msgpack":
            self._encode = msgpack.packb
            self._decode = msgpack.unpackb

    def _init_socket(self):
        ctx = zmq.Context()
        self._socket: zmq.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self._socket.connect(f"tcp://{self._host}:{self._port}")

    def _init_async_socket(self):
        ctx = zmq.asyncio.Context()
        self._socket: zmq.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self._socket.connect(f"tcp://{self._host}:{self._port}")

    def _set_socket_opt(self):
        self._socket.setsockopt(zmq.RCVTIMEO, self._default_timeout)
        self._socket.setsockopt(zmq.SNDTIMEO, self._default_timeout)
        self._socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages

    # quickle is removed as it is kind of broken for python objects, or my mere knowledge
    # def register_msg_types(self, classes: List[quickle.Struct]) -> None:
    #     """
    #     Add the list of `quickle.Struct` classes that will be sent in the call.
    #     Only effective for `quickle` serializer.
    #
    #     @param classes: List of Dataclass or python class that extends `quickle.Struct`
    #     """
    #     if self._serializer == "quickle":
    #         # enc = quickle.Encoder(registry=classes)
    #         # dec = quickle.Decoder(registry=classes)
    #         # self._encode = enc.dumps
    #         # self._decode = dec.loads
    #         pass

    def call(self, rpc_method_name: str, msg):
        """
        Call the rpc method of the ZeroServer.

        @param rpc_method_name:
        Method name should be string. This method should reside on the ZeroServer to get a successful response.

        @param msg:
        For msgpack serializer, msg should be base Python types. Cannot be objects.

        @return:
        Returns the response of ZeroServer's rpc method.
        """
        try:
            self._socket.send_multipart(
                [rpc_method_name.encode(), self._encode(msg)], zmq.DONTWAIT
            )
            resp = self._socket.recv()
            return self._decode(resp)
        except Exception as e:
            self._socket.close()
            self._init_socket()
            logging.exception(e)

    async def call_async(self, rpc_method_name: str, msg):
        """
        Async version of the `call`.

        @param rpc_method_name:
        Method name should be string. This method should reside on the ZeroServer to get a successful response.

        @param msg:
        For msgpack serializer, msg should be base Python types. Cannot be objects.

        @return:
        Returns the response of ZeroServer's rpc method.
        """
        try:
            await self._socket.send_multipart(
                [rpc_method_name.encode(), self._encode(msg)], zmq.DONTWAIT
            )
            resp = await self._socket.recv()
            return self._decode(resp)
        except Exception as e:
            self._socket.close()
            self._init_async_socket()
            logging.exception(e)
