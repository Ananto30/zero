SERVER_PROCESSING_ERROR = (
    "server cannot process message, check server logs for more details"
)


class ZeroException(Exception):
    pass


class MethodNotFoundException(ZeroException):
    pass


class TimeoutException(ZeroException):
    pass


class ConnectionException(ZeroException):
    pass


class RemoteException(Exception):
    pass
