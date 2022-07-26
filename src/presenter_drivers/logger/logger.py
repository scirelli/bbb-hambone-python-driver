import logging
import traceback
from json import JSONEncoder
from logging import Logger, basicConfig
from sys import stdout
from typing import Any, Dict, Union

from pythonjsonlogger import jsonlogger  # type: ignore

from ..environment import LOGLEVEL

log_level: int = getattr(logging, LOGLEVEL, logging.INFO)
log_level = log_level if log_level else logging.INFO

basicConfig(level=log_level)


def json_translate(obj: Any) -> Union[Dict[str, Any], None]:
    if isinstance(obj, BaseException):
        return error_to_dict(obj)
    return None


def create_logger(
    name: str, log_level: int = log_level  # pylint: disable=redefined-outer-name
) -> Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    return logger


def create_file_logger(
    name: str,
    filename: str,
    log_level: int = log_level,  # pylint: disable=redefined-outer-name
) -> Logger:
    logger = create_logger(name, log_level)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    return logger


def get_json_logger(
    name: str, log_level: int = log_level  # pylint: disable=redefined-outer-name
) -> Logger:
    """
    Fix multiple logging with
    logging.basicConfig(level=log_level, handlers=[_create_log_handler()])
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(_create_log_handler())
    logger.propagate = False

    return logger


def _create_log_handler() -> logging.StreamHandler:  # type: ignore
    json_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        json_default=json_translate,
        json_encoder=JSONEncoder,
        fmt="%(asctime)s %(levelname)s %(aws_request_id)s %(name)s %(message)s",
    )
    json_handler.setFormatter(formatter)

    return json_handler


def error_to_dict(e: BaseException) -> Dict[str, str]:
    return {
        "errorMsg": str(e),
        "stacktrace": "".join(traceback.TracebackException.from_exception(e).format()),
    }
