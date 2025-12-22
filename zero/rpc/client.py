from typing import Optional, Type, TypeVar

from zero.encoder import Encoder
from zero.encoder.generic import GenericEncoder
from zero.error import MethodNotFoundException, RemoteException, ValidationException
from zero.protocols.blueprint import AsyncZeroClientProtocol, ZeroClientProtocol
from zero.protocols.zeromq.client import AsyncZMQClient, ZMQClient
from zero.utils.type_util import AllowedType

T = TypeVar("T")


class ZeroClient:
    def __init__(
        self,
        host: str,
        port: int,
        default_timeout: int = 5000,
        encoder: Type[Encoder] = GenericEncoder,
        protocol: Type[ZeroClientProtocol] = ZMQClient,
        pool_size: int = 50,
    ):
        """
        ZeroClient provides the client interface for calling the ZeroServer.

        Zero usually use tcp protocol for communication. So a connection needs to
        be established to make a call. The connection creation is done lazily.
        So the first call will take some time to establish the connection.

        If the connection is dropped the client might timeout. But in the next
        call the connection will be re-established if the server is up.

        For different threads/processes, different connections are created.

        Parameters
        ----------
        host: str
            Host of the ZeroServer.

        port: int
            Port of the ZeroServer.

        default_timeout: int
            Default timeout for all calls. Default is 2000 ms.

        encoder: Type[Encoder]
            Encoder class to use for encoding/decoding messages from/to client.
            Default is GenericEncoder.
            If any other encoder is used, make sure the server should use the same encoder.
            Implement custom encoder by inheriting from `zero.encoder.Encoder`.

        protocol: Type[ZeroClientProtocol]
            Protocol client class to use for communication.
            Default is ZMQClient.
            Must implement the ZeroClientProtocol interface.

        pool_size: int
            Size of the connection pool. Default is 50.
        """
        self._address = f"tcp://{host}:{port}"
        self._default_timeout = default_timeout

        if not isinstance(encoder, type) or not issubclass(encoder, Encoder):
            raise TypeError(f"encoder should be a subclass of Encoder; not {encoder}")

        if not isinstance(protocol, type) or not issubclass(
            protocol, ZeroClientProtocol
        ):
            raise TypeError(
                f"protocol should be a subclass of ZeroClientProtocol; not {protocol}"
            )

        self._encoder = encoder()
        self._client_inst = protocol(
            self._address,
            self._default_timeout,
            self._encoder,
            pool_size,
        )

    def call(
        self,
        rpc_func_name: str,
        msg: AllowedType,
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> T:
        """
        Call the rpc function resides on the ZeroServer.

        Parameters
        ----------
        rpc_func_name: str
            Function name should be string.
            This funtion should reside on the ZeroServer to get a successful response.

        msg: Union[int, float, str, dict, list, tuple, None]
            The only argument of the rpc function.
            This should be of the same type as the rpc function's argument.

        timeout: Optional[int]
            Timeout for the call. In milliseconds.
            Default is 2000 milliseconds.

        return_type: Optional[Type[T]]
            The return type of the rpc function.
            If return_type is set, the response will be parsed to the return_type.

        Returns
        -------
        T
            The return value of the rpc function.
            If return_type is set, the response will be parsed to the return_type.

        Raises
        ------
        TimeoutException
            If the call times out or the connection is dropped.

        MethodNotFoundException
            If the rpc function is not found on the ZeroServer.

        ConnectionException
            If zeromq connection is not established.
            Or zeromq cannot send the message to the server.
            Or zeromq cannot receive the response from the server.
            Mainly represents zmq.error.Again exception.
        """
        resp_data = self._client_inst.call(rpc_func_name, msg, timeout, return_type)
        check_response(resp_data)
        return resp_data  # type: ignore

    def close(self):
        self._client_inst.close()


class AsyncZeroClient:
    def __init__(
        self,
        host: str,
        port: int,
        default_timeout: int = 5000,
        encoder: Type[Encoder] = GenericEncoder,
        protocol: Type[AsyncZeroClientProtocol] = AsyncZMQClient,
        pool_size: int = 50,
    ):
        """
        AsyncZeroClient provides the asynchronous client interface for calling the ZeroServer.
        Python's async/await can be used to make the calls.
        Naturally async client is faster.

        Zero use tcp protocol for communication.
        So a connection needs to be established to make a call.
        The connection creation is done lazily.
        So the first call will take some time to establish the connection.
        If the connection is dropped the client might timeout.
        But in the next call the connection will be re-established.

        For different threads/processes, different connections are created.

        Parameters
        ----------
        host: str
            Host of the ZeroServer.

        port: int
            Port of the ZeroServer.

        default_timeout: int
            Default timeout for all calls in milliseconds.
            Default is 2000 milliseconds (2 seconds).

        encoder: Type[Encoder]
            Encoder class to use for encoding/decoding messages from/to client.
            Default is GenericEncoder.
            If any other encoder is used, the server should use the same encoder.
            Implement custom encoder by inheriting from `zero.encoder.Encoder`.

        protocol: Type[AsyncZeroClientProtocol]
            Protocol client class to use for communication.
            Default is AsyncZMQClient.
            Must implement the AsyncZeroClientProtocol interface.

        pool_size: int
            Size of the connection pool. Default is 50.
        """
        self._address = f"tcp://{host}:{port}"
        self._default_timeout = default_timeout

        if not isinstance(encoder, type) or not issubclass(encoder, Encoder):
            raise TypeError(f"encoder should be a subclass of Encoder; not {encoder}")

        if not isinstance(protocol, type) or not issubclass(
            protocol, AsyncZeroClientProtocol
        ):
            raise TypeError(
                f"protocol should be a subclass of AsyncZeroClientProtocol; not {protocol}"
            )

        self._encoder = encoder()
        self._client_inst = protocol(
            self._address,
            self._default_timeout,
            self._encoder,
            pool_size,
        )

    async def call(
        self,
        rpc_func_name: str,
        msg: AllowedType,
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> T:
        """
        Call the rpc function resides on the ZeroServer.

        Parameters
        ----------
        rpc_func_name: str
            Function name should be string.
            This funtion should reside on the ZeroServer to get a successful response.

        msg: Union[int, float, str, dict, list, tuple, None]
            The only argument of the rpc function.
            This should be of the same type as the rpc function's argument.

        timeout: Optional[int]
            Timeout for the call. In milliseconds.
            Default is 2000 milliseconds.

        return_type: Optional[Type[T]]
            The return type of the rpc function.
            If return_type is set, the response will be parsed to the return_type.

        Returns
        -------
        T
            The return value of the rpc function.
            If return_type is set, the response will be parsed to the return_type.

        Raises
        ------
        TimeoutException
            If the call times out or the connection is dropped.

        MethodNotFoundException
            If the rpc function is not found on the ZeroServer.

        ConnectionException
            If zeromq connection is not established.
            Or zeromq cannot send the message to the server.
            Or zeromq cannot receive the response from the server.
            Mainly represents zmq.error.Again exception.
        """
        _timeout = timeout or self._default_timeout
        resp_data = await self._client_inst.call(
            rpc_func_name, msg, _timeout, return_type
        )
        check_response(resp_data)
        return resp_data  # type: ignore

    def close(self):
        self._client_inst.close()


def check_response(resp_data):
    if isinstance(resp_data, dict):
        if exc := resp_data.get("__zerror__function_not_found"):
            raise MethodNotFoundException(exc)
        if exc := resp_data.get("__zerror__server_exception"):
            raise RemoteException(exc)
        if exc := resp_data.get("__zerror__validation_error"):
            raise ValidationException(exc)
