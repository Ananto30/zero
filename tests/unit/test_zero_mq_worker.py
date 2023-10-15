import unittest
from unittest.mock import Mock, patch

import pytest
import zmq

from zero.zero_mq.queue_device.worker import ZeroMQWorker


class TestWorker(unittest.TestCase):
    def test_create_zeromq_worker(self):
        worker = ZeroMQWorker(1)
        self.assertIsInstance(worker, ZeroMQWorker)
        self.assertEqual(worker.worker_id, 1)
        # self.assertEqual(worker.context, zmq.Context.instance())
        # self.assertEqual(worker.socket, worker.context.socket(zmq.DEALER))
        self.assertIsNotNone(worker.context)
        self.assertIsNotNone(worker.socket)
        self.assertEqual(worker.socket.getsockopt(zmq.LINGER), 0)
        self.assertEqual(worker.socket.getsockopt(zmq.SNDTIMEO), 2000)
        self.assertEqual(worker.socket.getsockopt(zmq.RCVTIMEO), -1)
        worker.close()
        self.assertEqual(worker.socket.closed, True)
        self.assertEqual(worker.context.closed, True)

    @pytest.mark.skip(reason="hard to test infinite loop")
    async def test_listen_timeout(self):
        worker = ZeroMQWorker(1)
        mock_msg_handler = Mock(return_value=b"response")
        with (
            patch.object(worker.socket, "connect", return_value=None),
            patch.object(worker, "_recv_and_process", side_effect=zmq.error.Again),
        ):
            await worker.listen("tcp://example.com:5555", mock_msg_handler)

    async def test_recv_and_process(self):
        worker = ZeroMQWorker(1)
        mock_msg_handler = Mock(return_value=b"response")
        with patch.object(
            worker.socket, "recv_multipart", return_value=[b"ident", b"request"]
        ) as mock_recv_multipart, patch.object(
            worker.socket, "send_multipart", return_value=None
        ) as mock_send_multipart:
            await worker._recv_and_process(mock_msg_handler)
            mock_msg_handler.assert_called_once()
            mock_recv_multipart.assert_called_once()
            mock_send_multipart.assert_called_once()

    async def test_recv_and_process_invalid_message(self):
        worker = ZeroMQWorker(1)
        mock_msg_handler = Mock(return_value=b"response")
        with patch.object(
            worker.socket, "recv_multipart", return_value=[b"ident"]
        ) as mock_recv_multipart, patch.object(
            worker.socket, "send_multipart", return_value=None
        ) as mock_send_multipart:
            await worker._recv_and_process(mock_msg_handler)
            mock_msg_handler.assert_not_called()
            mock_send_multipart.assert_not_called()
            mock_recv_multipart.assert_called_once()
