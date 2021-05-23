def check_allowed_types(msg):
    if isinstance(msg, dict) or isinstance(msg, str) or isinstance(msg, int) or isinstance(msg, float) or isinstance(msg, bool):
        pass
    else:
        raise Exception("`msg` should be any of dict, str, int, float, bool type")
