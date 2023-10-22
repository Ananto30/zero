import sys
import unittest
from typing import Any, Tuple
from unittest.mock import patch

# import pytest
import zmq

from zero import ZeroServer
from zero.encoder.protocols import Encoder
from zero.zero_mq.protocols import ZeroMQBroker

DEFAULT_PORT = 5559
DEFAULT_HOST = "0.0.0.0"


class TestServer(unittest.TestCase):
    def test_create_default_server(self):
        server = ZeroServer()
        self.assertIsInstance(server, ZeroServer)
        self.assertEqual(server._port, DEFAULT_PORT)
        self.assertEqual(server._host, DEFAULT_HOST)
        self.assertEqual(server._address, f"tcp://{DEFAULT_HOST}:{DEFAULT_PORT}")
        self.assertIsInstance(server._encoder, Encoder)
        self.assertEqual(server._rpc_router, {})
        self.assertEqual(server._rpc_input_type_map, {})
        self.assertEqual(server._rpc_return_type_map, {})

    def test_create_server_with_port(self):
        port = 5560
        server = ZeroServer(port=port)
        self.assertIsInstance(server, ZeroServer)
        self.assertEqual(server._port, port)
        self.assertEqual(server._host, DEFAULT_HOST)
        self.assertEqual(server._address, f"tcp://{DEFAULT_HOST}:{port}")
        self.assertIsInstance(server._encoder, Encoder)
        self.assertEqual(server._rpc_router, {})
        self.assertEqual(server._rpc_input_type_map, {})
        self.assertEqual(server._rpc_return_type_map, {})

    def test_create_server_with_host(self):
        host = "123.0.0.123"
        server = ZeroServer(host=host)
        self.assertIsInstance(server, ZeroServer)
        self.assertEqual(server._port, DEFAULT_PORT)
        self.assertEqual(server._host, host)
        self.assertEqual(server._address, f"tcp://{host}:{DEFAULT_PORT}")
        self.assertIsInstance(server._encoder, Encoder)
        self.assertEqual(server._rpc_router, {})
        self.assertEqual(server._rpc_input_type_map, {})
        self.assertEqual(server._rpc_return_type_map, {})

    def test_create_server_with_host_and_port(self):
        host = "123.0.0.124"
        port = 5561
        server = ZeroServer(host=host, port=port)
        self.assertIsInstance(server, ZeroServer)
        self.assertEqual(server._port, port)
        self.assertEqual(server._host, host)
        self.assertEqual(server._address, f"tcp://{host}:{port}")
        self.assertIsInstance(server._encoder, Encoder)
        self.assertEqual(server._rpc_router, {})
        self.assertEqual(server._rpc_input_type_map, {})
        self.assertEqual(server._rpc_return_type_map, {})

    def test_create_server_with_encoder(self):
        class CustomEncoder:
            def encode(self, message: Any) -> bytes:
                return message

            def decode(self, message: bytes) -> Any:
                return message

            def decode_type(self, message: bytes, typ: Any) -> Any:
                return message

        encoder = CustomEncoder()

        server = ZeroServer(encoder=encoder)
        self.assertIsInstance(server, ZeroServer)
        self.assertEqual(server._port, DEFAULT_PORT)
        self.assertEqual(server._host, DEFAULT_HOST)
        self.assertEqual(server._address, f"tcp://{DEFAULT_HOST}:{DEFAULT_PORT}")
        self.assertIsInstance(server._encoder, Encoder)
        self.assertEqual(server._rpc_router, {})
        self.assertEqual(server._rpc_input_type_map, {})
        self.assertEqual(server._rpc_return_type_map, {})

    def test_create_server_with_encoder_and_port(self):
        class CustomEncoder:
            def encode(self, message: Any) -> bytes:
                return message

            def decode(self, message: bytes) -> Any:
                return message

            def decode_type(self, message: bytes, typ: Any) -> Any:
                return message

        encoder = CustomEncoder()
        port = 5562

        server = ZeroServer(encoder=encoder, port=port)
        self.assertIsInstance(server, ZeroServer)
        self.assertEqual(server._port, port)
        self.assertEqual(server._host, DEFAULT_HOST)
        self.assertEqual(server._address, f"tcp://{DEFAULT_HOST}:{port}")
        self.assertIsInstance(server._encoder, Encoder)
        self.assertEqual(server._rpc_router, {})
        self.assertEqual(server._rpc_input_type_map, {})
        self.assertEqual(server._rpc_return_type_map, {})

    def test_create_server_with_encoder_and_host(self):
        class CustomEncoder:
            def encode(self, message: Any) -> bytes:
                return message

            def decode(self, message: bytes) -> Any:
                return message

            def decode_type(self, message: bytes, typ: Any) -> Any:
                return message

        encoder = CustomEncoder()
        host = "123.0.0.123"

        server = ZeroServer(encoder=encoder, host=host)
        self.assertIsInstance(server, ZeroServer)
        self.assertEqual(server._port, DEFAULT_PORT)
        self.assertEqual(server._host, host)
        self.assertEqual(server._address, f"tcp://{host}:{DEFAULT_PORT}")
        self.assertIsInstance(server._encoder, Encoder)
        self.assertEqual(server._rpc_router, {})
        self.assertEqual(server._rpc_input_type_map, {})
        self.assertEqual(server._rpc_return_type_map, {})

    def test_create_server_with_encoder_and_host_and_port(self):
        class CustomEncoder:
            def encode(self, message: Any) -> bytes:
                return message

            def decode(self, message: bytes) -> Any:
                return message

            def decode_type(self, message: bytes, typ: Any) -> Any:
                return message

        encoder = CustomEncoder()
        host = "123.0.0.123"
        port = 5563

        server = ZeroServer(encoder=encoder, host=host, port=port)
        self.assertIsInstance(server, ZeroServer)
        self.assertEqual(server._port, port)
        self.assertEqual(server._host, host)
        self.assertEqual(server._address, f"tcp://{host}:{port}")
        self.assertIsInstance(server._encoder, Encoder)
        self.assertEqual(server._rpc_router, {})
        self.assertEqual(server._rpc_input_type_map, {})
        self.assertEqual(server._rpc_return_type_map, {})

    def test_register_rpc(self):
        server = ZeroServer()

        @server.register_rpc
        def add(msg: Tuple[int, int]) -> int:
            return msg[0] + msg[1]

        self.assertEqual(server._rpc_router, {"add": add})
        self.assertEqual(server._rpc_input_type_map, {"add": Tuple[int, int]})
        self.assertEqual(server._rpc_return_type_map, {"add": int})

    def test_register_same_rpc_twice(self):
        server = ZeroServer()

        @server.register_rpc
        def add(msg: Tuple[int, int]) -> int:
            return msg[0] + msg[1]

        with self.assertRaises(ValueError):
            server.register_rpc(add)

    def test_register_rpc_with_invalid_input_type(self):
        server = ZeroServer()

        class Message:
            msg: str

        with self.assertRaises(TypeError):

            @server.register_rpc
            def add(msg: Message) -> int:
                return 1

    def test_register_rpc_with_invalid_return_type(self):
        server = ZeroServer()

        class Message:
            msg: str

        with self.assertRaises(TypeError):

            @server.register_rpc
            def add(msg: Tuple[int, int]) -> Message:
                return Message("1")

    def test_register_rpc_with_invalid_input_type_and_return_type(self):
        server = ZeroServer()

        class Message:
            msg: str

        with self.assertRaises(TypeError):

            @server.register_rpc
            def add(msg: Message) -> Message:
                return Message()

    def test_server_run(self):
        server = ZeroServer()

        @server.register_rpc
        def add(msg: Tuple[int, int]) -> int:
            return msg[0] + msg[1]

        with patch("zmq.device") as mock_device:
            with self.assertRaises(SystemExit):
                server.run()
                self.assertIsInstance(server._broker, ZeroMQBroker)
                if sys.platform == "win32":
                    self.assertIn("tcp", server._device_comm_channel)
                else:
                    self.assertIn("ipc", server._device_comm_channel)
                mock_device.assert_called_once_with(
                    zmq.QUEUE,
                    server._broker.gateway,  # type: ignore
                    server._broker.backend,  # type: ignore
                )

    # @pytest.mark.skipif(sys.platform == "win32", reason="Does not run on windows")
    # @pytest.mark.skip
    def test_server_run_keyboard_interrupt(self):
        server = ZeroServer()

        @server.register_rpc
        def add(msg: Tuple[int, int]) -> int:
            return msg[0] + msg[1]

        with patch.object(server, "_start_server", side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit):
                server.run()
