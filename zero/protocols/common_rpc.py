import logging
from typing import Any, Callable, Dict, Optional, Tuple

from zero.codegen.codegen import CodeGen


def execute_common_rpc(
    func_name: str,
    msg: Any,
    rpc_router: Dict[str, Tuple[Callable, bool]],
    rpc_input_type_map: Dict[str, Optional[type]],
    rpc_return_type_map: Dict[str, Optional[type]],
) -> Any:
    if func_name == "get_rpc_contract":
        return _generate_rpc_contract(
            msg,
            rpc_router,
            rpc_input_type_map,
            rpc_return_type_map,
        )

    if func_name == "connect":
        return "connected"

    if func_name not in rpc_router:
        logging.error("Function `%s` not found!", func_name)
        return {"__zerror__function_not_found": f"Function `{func_name}` not found!"}

    return None


def _generate_rpc_contract(
    msg,
    rpc_router: Dict[str, Tuple[Callable, bool]],
    rpc_input_type_map: Dict[str, Optional[type]],
    rpc_return_type_map: Dict[str, Optional[type]],
):
    try:
        codegen = CodeGen(
            rpc_router,
            rpc_input_type_map,
            rpc_return_type_map,
        )
        return codegen.generate_code(msg[0], msg[1], msg[2], msg[3])

    except Exception as exc:  # pylint: disable=broad-except
        logging.exception(exc)
        return {"__zerror__failed_to_generate_client_code": str(exc)}
