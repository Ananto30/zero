def check_allowed_types(msg):
    if isinstance(msg, dict) or isinstance(msg, str) or isinstance(msg, int) or isinstance(msg, float) or isinstance(msg, bool) or isinstance(msg, list):
        pass
    else:
        raise Exception("`msg` should be any of dict, str, int, float, bool, list type")


class SingletonMeta(type):
    _instance = None

    def __call__(self):
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance
