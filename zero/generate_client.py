import argparse
import os

from .rpc.client import ZeroClient


def generate_client_code_and_save(host, port, directory, overwrite_dir=False):
    zero_client = ZeroClient(host, port)
    code = zero_client.call("get_rpc_contract", [host, port])

    if isinstance(code, dict) and "__zerror__failed_to_generate_client_code" in code:
        print(
            f"Failed to generate client code: {code['__zerror__failed_to_generate_client_code']}"
        )
        return

    if directory != ".":
        if not os.path.exists(directory):
            os.makedirs(directory)
        elif not overwrite_dir:
            print()
            answer = input(
                f"Directory {directory} already exists, do you like to overwrite it? [y/N]: "
            )
            if answer.lower() != "y":
                return

    with open(directory + "/rpc_client.py", "w", encoding="utf-8") as fp:
        fp.write(code)


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    # remove default group
    parser._action_groups.pop()  # pylint: disable=protected-access
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    parser.add_argument("directory")
    required.add_argument("--host", required=True)
    required.add_argument("--port", required=True, type=int)
    optional.add_argument("--overwrite-dir", action="store_true")
    args = parser.parse_args()
    generate_client_code_and_save(
        args.host,
        args.port,
        args.directory,
        args.overwrite_dir,
    )
