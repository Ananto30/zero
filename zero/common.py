def check_allowed_types(msg, rpc_method=None):
    if isinstance(msg, (dict, str, int, float, bool, list, tuple)):
        pass
    else:
        if rpc_method:
            raise Exception(f"return of `{rpc_method}` should be any of dict, str, int, float, bool, list type; found {type(msg)}")
        else:
            raise Exception(f"`msg` should be any of dict, str, int, float, bool, list type; not {type(msg)}")


class SingletonMeta(type):
    _instance = None

    def __call__(self):
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance
