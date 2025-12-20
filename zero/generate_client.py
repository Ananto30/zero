import argparse
import asyncio
import os

from .protocols.tcp import AsyncTCPClient
from .protocols.zeromq import AsyncZMQClient
from .rpc.client import AsyncZeroClient


async def generate_client_code_and_save(
    host,
    port,
    directory,
    protocol,
    async_client=False,
    overwrite_dir=False,
):
    if protocol == "tcp":
        # TCP protocol always uses async client
        async_client = True
        zero_client = AsyncZeroClient(host, port, protocol=AsyncTCPClient)
    elif protocol == "zmq":
        zero_client = AsyncZeroClient(host, port, protocol=AsyncZMQClient)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")

    code = await zero_client.call(
        "get_rpc_contract", [host, port, protocol, async_client], timeout=10000
    )

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
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to save generated client code",
    )
    required.add_argument(
        "--host",
        required=True,
        type=str,
        help="Server host",
    )
    required.add_argument(
        "--port",
        required=True,
        type=int,
        help="Server port",
    )
    optional.add_argument(
        "--protocol",
        choices=["zmq", "tcp"],
        required=True,
        help="Protocol to use",
    )
    optional.add_argument(
        "--overwrite-dir",
        action="store_true",
        help="Overwrite existing directory",
    )
    optional.add_argument(
        "--async",
        dest="async_client",
        action="store_true",
        default=False,
        help="Generate async client code (default is sync for zmq, always async for tcp)",
    )
    args = parser.parse_args()

    asyncio.run(
        generate_client_code_and_save(
            args.host,
            args.port,
            args.directory,
            protocol=args.protocol,
            async_client=args.async_client,
            overwrite_dir=args.overwrite_dir,
        )
    )
