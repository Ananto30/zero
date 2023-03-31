import asyncio
import logging
from typing import Any, Dict, Optional, Union

import zero.config as config
from zero.encoder import Encoder, get_encoder
from zero.error import MethodNotFoundException, TimeoutException
from zero.utils.util import current_time_us, unique_id
from zero.zero_mq import AsyncZeroMQClient, ZeroMQClient, get_async_client, get_client
from zero.zero_mq.helpers import zpipe


class ZeroClient:
    def __init__(
        self,
        host: str,
        port: int,
        default_timeout: int = 2000,
        encoder: Optional[Encoder] = None,
    ):
        """
        ZeroClient provides the client interface for calling the ZeroServer.

        @param host:
        Host of the ZeroServer.

        @param port:
        Port of the ZeroServer.

        @param default_timeout:
        Default timeout for each call. In milliseconds.
        """
        self._address = f"tcp://{host}:{port}"
        self._default_timeout = default_timeout
        self.encdr = encoder or get_encoder(config.ENCODER)

        self.zmq: ZeroMQClient = None  # type: ignore

    def _init(self):
        self.zmq = get_client(config.ZEROMQ_PATTERN, self._default_timeout)
        self.zmq.connect(self._address)

        self.peer1, self.peer2 = zpipe(self.zmq.context)

    def close(self):
        if self.zmq is not None:
            self.zmq.close()
            self.zmq = None  # type: ignore

    def _ensure_conntected(self):
        if self.zmq is not None:
            return

        self._init()
        self.try_connect()

    def try_connect(self):
        frames = [unique_id(), "connect", ""]
        self.zmq.send(self.encdr.encode(frames))
        self.encdr.decode(self.zmq.recv())
        logging.info(f"Connected to server at {self._address}")

    def call(
        self,
        rpc_method_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Call the rpc method of the ZeroServer.

        @param rpc_method_name:
        Method name should be string. This method should reside on the ZeroServer to get a successful response.

        @param msg:
        For msgpack serializer, msg should be base Python types. Cannot be objects.

        @param timeout:
        Timeout for the call. In milliseconds.

        @return:
        Returns the response of ZeroServer's rpc method.
        """
        self._ensure_conntected()

        _timeout = self._default_timeout if timeout is None else timeout

        def _poll_data():
            if not self.zmq.poll(_timeout):
                raise TimeoutException(f"Timeout while sending message at {self._address}")

            resp_id, resp_data = self.encdr.decode(self.zmq.recv())
            return resp_id, resp_data

        req_id = unique_id()
        frames = [req_id, rpc_method_name, "" if msg is None else msg]
        self.zmq.send(self.encdr.encode(frames))

        resp_id, resp_data = None, None
        while resp_id != req_id:
            resp_id, resp_data = _poll_data()

        if isinstance(resp_data, dict) and "__zerror__method_not_found" in resp_data:
            raise MethodNotFoundException(resp_data.get("__zerror__method_not_found"))

        return resp_data


class AsyncZeroClient:
    def __init__(
        self,
        host: str,
        port: int,
        default_timeout: int = 2000,
        encoder: Optional[Encoder] = None,
    ):
        """
        AsyncZeroClient provides the asynchronous client interface for calling the ZeroServer.
        You can use Python's async/await with this client.
        Naturally async client is faster.

        @param host:
        Host of the ZeroServer.

        @param port:
        Port of the ZeroServer.

        @param default_timeout:
        Default timeout for each call. In milliseconds.
        """
        self._address = f"tcp://{host}:{port}"
        self._default_timeout = default_timeout
        self._encoder = encoder or get_encoder(config.ENCODER)

        self.zmq_client: AsyncZeroMQClient = None  # type: ignore

    def _init(self):
        self.zmq_client = get_async_client(config.ZEROMQ_PATTERN, self._default_timeout)
        self.zmq_client.connect(self._address)

        self.__resps: Dict[str, Any] = {}

    def close(self):
        if self.zmq_client is not None:
            self.zmq_client.close()
            self.zmq_client = None  # type: ignore
            self.__resps = {}

    async def _ensure_connected(self):
        if self.zmq_client is not None:
            return

        self._init()
        await self.try_connect()

    async def try_connect(self):
        frames = [unique_id(), "connect", ""]
        await self.zmq_client.send(self._encoder.encode(frames))
        self._encoder.decode(await self.zmq_client.recv())
        logging.info(f"Connected to server at {self._address}")

    async def call(
        self,
        rpc_method_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Call the rpc method of the ZeroServer.

        @param rpc_method_name:
        Method name should be string. This method should reside on the ZeroServer to get a successful response.

        @param msg:
        For msgpack serializer, msg should be base Python types. Cannot be objects.

        @param timeout:
        Timeout for the call. In milliseconds.

        @return:
        Returns the response of ZeroServer's rpc method.
        """
        await self._ensure_connected()

        _timeout = self._default_timeout if timeout is None else timeout
        expire_at = current_time_us() + (_timeout * 1000)

        async def _poll_data():
            # TODO async has issue with poller, after 3-4 calls, it returns empty
            # if not await self.zmq_client.poll(_timeout):
            #     raise TimeoutException(f"Timeout while sending message at {self._address}")

            resp = await self.zmq_client.recv()
            resp_id, resp_data = self._encoder.decode(resp)
            self.__resps[resp_id] = resp_data

        req_id = unique_id()
        frames = [req_id, rpc_method_name, "" if msg is None else msg]
        await self.zmq_client.send(self._encoder.encode(frames))

        # every request poll the data, so whenever a response comes, it will be stored in __resps
        # dont need to poll again in the while loop
        await _poll_data()

        while req_id not in self.__resps and current_time_us() < expire_at:
            await asyncio.sleep(1e-6)

        if current_time_us() > expire_at:
            raise TimeoutException(f"Timeout while waiting for response at {self._address}")

        print(expire_at, current_time_us(), self.__resps)
        resp_data = self.__resps.pop(req_id)

        if isinstance(resp_data, dict) and "__zerror__method_not_found" in resp_data:
            raise MethodNotFoundException(resp_data.get("__zerror__method_not_found"))

        return resp_data
