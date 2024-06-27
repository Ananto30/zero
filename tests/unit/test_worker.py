import unittest
from unittest.mock import MagicMock, Mock, patch

import msgspec

from zero.encoder.protocols import Encoder
from zero.error import SERVER_PROCESSING_ERROR
from zero.protocols.zeromq.worker import _Worker


class TestWorker(unittest.TestCase):
    def setUp(self):
        self.rpc_router = {
            "get_rpc_contract": (Mock(), False),
            "connect": (Mock(), False),
            "some_function": (Mock(), True),  # Assuming this is now an async function
        }
        self.device_comm_channel = "tcp://example.com:5555"
        self.encoder = Mock()
        self.rpc_input_type_map = {}
        self.rpc_return_type_map = {}

    @patch("asyncio.new_event_loop")
    def test_start_dealer_worker(self, mock_event_loop):
        worker_id = 1
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )

        with patch("zero.protocols.zeromq.worker.get_worker") as mock_get_worker:
            mock_worker = mock_get_worker.return_value
            worker.start_dealer_worker(worker_id)

            mock_get_worker.assert_called_once_with("proxy", worker_id)
            mock_worker.listen.assert_called_once()
            mock_worker.close.assert_called_once()

    @patch("zero.protocols.zeromq.worker.get_worker")
    def test_start_dealer_worker_exception_handling(self, mock_get_worker):
        mock_worker = Mock()
        mock_get_worker.return_value = mock_worker
        mock_worker.listen.side_effect = Exception("Test Exception")

        worker_id = 1
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )

        with self.assertLogs(level="ERROR") as log:
            worker.start_dealer_worker(worker_id)
            self.assertIn("Test Exception", log.output[0])
        mock_worker.close.assert_called_once()

    @patch("zero.protocols.zeromq.worker.get_worker")
    def test_start_dealer_worker_keyboard_interrupt_handling(self, mock_get_worker):
        mock_worker = Mock()
        mock_get_worker.return_value = mock_worker
        mock_worker.listen.side_effect = KeyboardInterrupt

        worker_id = 1
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )

        with self.assertLogs(level="WARNING") as log:
            worker.start_dealer_worker(worker_id)
            self.assertIn("terminating worker", log.output[0])
        mock_worker.close.assert_called_once()

    @patch("zero.protocols.zeromq.worker.async_to_sync", side_effect=lambda x: x)
    def test_handle_msg_get_rpc_contract(self, mock_async_to_sync):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )
        msg = ["rpc_name", "msg_data"]
        expected_response = b"generated_code"

        with patch.object(
            worker, "generate_rpc_contract", return_value=expected_response
        ) as mock_generate_rpc_contract:
            response = worker.execute_rpc("get_rpc_contract", msg)

            mock_generate_rpc_contract.assert_called_once_with(msg)
            self.assertEqual(response, expected_response)

    @patch("zero.protocols.zeromq.worker.async_to_sync", side_effect=lambda x: x)
    def test_handle_msg_rpc_call_exception(self, mock_async_to_sync):
        self.rpc_router["failing_function"] = (
            Mock(side_effect=Exception("RPC Exception")),
            False,
        )
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )

        response = worker.execute_rpc("failing_function", "msg")
        self.assertEqual(
            response, {"__zerror__server_exception": "Exception('RPC Exception')"}
        )

    def test_handle_msg_connect(self):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )
        msg = "some_message"
        expected_response = "connected"

        response = worker.execute_rpc("connect", msg)

        self.assertEqual(response, expected_response)

    def test_handle_msg_function_not_found(self):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )
        msg = "some_message"
        expected_response = {
            "__zerror__function_not_found": "Function `some_function_not_found` not found!"
        }

        response = worker.execute_rpc("some_function_not_found", msg)

        self.assertEqual(response, expected_response)

    def test_handle_msg_server_exception(self):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )
        msg = "some_message"
        expected_response = {
            "__zerror__server_exception": "Exception('Exception occurred')"
        }

        with patch(
            "zero.protocols.zeromq.worker.async_to_sync",
            side_effect=Exception("Exception occurred"),
        ):
            response = worker.execute_rpc("some_function", msg)

        self.assertEqual(response, expected_response)

    def test_generate_rpc_contract(self):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )
        msg = ["rpc_name", "msg_data"]
        expected_response = b"generated_code"

        with patch.object(
            worker.codegen, "generate_code", return_value=expected_response
        ) as mock_generate_code:
            response = worker.generate_rpc_contract(msg)

            mock_generate_code.assert_called_once_with("rpc_name", "msg_data")
            self.assertEqual(response, expected_response)

    def test_generate_rpc_contract_exception_handling(self):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )

        with patch.object(
            worker.codegen, "generate_code", side_effect=Exception("Codegen Exception")
        ):
            response = worker.generate_rpc_contract(["rpc_name", "msg_data"])
            self.assertEqual(
                response,
                {"__zerror__failed_to_generate_client_code": "Codegen Exception"},
            )


class TestWorkerSpawn(unittest.TestCase):
    def test_spawn_worker(self):
        mock_worker = MagicMock()

        rpc_router = {
            "get_rpc_contract": (Mock(), False),
            "connect": (Mock(), False),
            "some_function": (Mock(), True),
        }
        device_comm_channel = "tcp://example.com:5555"
        encoder = Mock()
        rpc_input_type_map = {}
        rpc_return_type_map = {}
        worker_id = 1

        with patch("zero.protocols.zeromq.worker._Worker") as mock_worker_class:
            mock_worker_class.return_value = mock_worker
            _Worker.spawn_worker(
                rpc_router,
                device_comm_channel,
                encoder,
                rpc_input_type_map,
                rpc_return_type_map,
                worker_id,
            )

            mock_worker_class.assert_called_once_with(
                rpc_router,
                device_comm_channel,
                encoder,
                rpc_input_type_map,
                rpc_return_type_map,
            )
            mock_worker.start_dealer_worker.assert_called_once_with(worker_id)


def some_function(msg: str) -> str:
    return msg


class TestWorkerHandleMsg(unittest.TestCase):
    def setUp(self):
        self.rpc_router = {
            "get_rpc_contract": (MagicMock(), False),
            "connect": (MagicMock(), False),
            "some_function": (some_function, False),
        }
        self.device_comm_channel = "tcp://example.com:5555"
        self.encoder = MagicMock(spec=Encoder)
        self.rpc_input_type_map = {
            "some_function": str,
        }
        self.rpc_return_type_map = {
            "some_function": str,
        }

    def test_handle_msg_with_valid_input(self):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )
        func_name_encoded = b"some_function"
        data = self.encoder.encode("msg_data")

        worker.execute_rpc = Mock()
        worker.execute_rpc.return_value = "response"
        self.encoder.decode_type.return_value = "msg_data"

        response = worker.handle_msg(func_name_encoded, data)

        worker.execute_rpc.assert_called_once_with(
            func_name_encoded.decode(), "msg_data"
        )
        self.encoder.encode.assert_called_with("response")
        self.assertEqual(response, self.encoder.encode.return_value)

    def test_handle_msg_with_validation_error(self):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )
        func_name_encoded = b"some_function"
        data = b"msg_data"
        expected_error = "__zerror__validation_error"
        expected_error_message = "Validation Error"
        expected_encoded_error = b"encoded_error"

        self.encoder.decode_type.side_effect = msgspec.ValidationError(
            expected_error_message
        )
        self.encoder.encode.return_value = expected_encoded_error

        response = worker.handle_msg(func_name_encoded, data)

        self.encoder.decode_type.assert_called_once_with(data, str)
        self.encoder.encode.assert_called_once_with(
            {expected_error: expected_error_message}
        )
        self.assertEqual(response, expected_encoded_error)
        self.assertEqual(response, expected_encoded_error)

    def test_handle_msg_with_server_exception(self):
        worker = _Worker(
            self.rpc_router,
            self.device_comm_channel,
            self.encoder,
            self.rpc_input_type_map,
            self.rpc_return_type_map,
        )
        func_name_encoded = b"some_function"
        data = self.encoder.encode("msg_data")

        worker.execute_rpc = Mock()
        worker.execute_rpc.side_effect = Exception("Server Exception")
        self.encoder.decode_type.return_value = "msg_data"

        worker.handle_msg(func_name_encoded, data)

        worker.execute_rpc.assert_called_once_with(
            func_name_encoded.decode(), "msg_data"
        )
        self.encoder.encode.assert_called_with(
            {"__zerror__server_exception": SERVER_PROCESSING_ERROR}
        )
