import logging

from zero.protocols.zeromq.client import AsyncZMQClient, ZMQClient
from zero.protocols.zeromq.server import ZMQServer

logging.basicConfig(
    format="%(asctime)s  %(levelname)8s  %(process)8d  %(module)s > %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)

RESERVED_FUNCTIONS = ["get_rpc_contract", "connect", "__server_info__"]
ZEROMQ_PATTERN = "proxy"
SUPPORTED_PROTOCOLS = {
    "zeromq": {
        "server": ZMQServer,
        "client": ZMQClient,
        "async_client": AsyncZMQClient,
    },
}
