import argparse
from .client import ZeroClient


def generate_client_code_and_save(host, port, directory):
    zero_client = ZeroClient(host, port, use_async=False)
    code = zero_client.call("get_rpc_contract", None)
    with open(directory + "/rpc_client.py", "w") as f:
        f.write(code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser._action_groups.pop()
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    parser.add_argument("directory")
    required.add_argument("--host", required=True)
    required.add_argument("--port", required=True, type=int)
    optional.add_argument("--optional_arg")
    args = parser.parse_args()
    generate_client_code_and_save(args.host, args.port, args.directory)
