import logging

logging.basicConfig(
    format="%(asctime)s  %(levelname)8s  %(process)8d  %(module)s > %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)

RESERVED_FUNCTIONS = ["get_rpc_contract", "connect", "__server_info__"]
ZEROMQ_PATTERN = "proxy"
