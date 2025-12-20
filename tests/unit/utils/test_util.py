import logging
import unittest
from unittest.mock import patch

from zero.utils.util import log_error


class TestLogError(unittest.TestCase):
    def test_log_error(self):
        @log_error
        def divide(a, b):
            return a / b

        with patch.object(logging, "exception") as mock_exception:
            result = divide(10, 2)
            self.assertEqual(result, 5)
            mock_exception.assert_not_called()

            result = divide(10, 0)
            self.assertIsNone(result)
            mock_exception.assert_called_once()
