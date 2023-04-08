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
