"""
Operations with bytes.
"""

from enum import Enum
import struct
import json
from typing import Any, Sequence, TypeVar

from pydantic import BaseModel, ValidationError

from error import CodeError
from codes import model_validation_error


ENCODING = "utf-8"
T_Model = TypeVar("T_Model", bound=BaseModel)


def bytes_to_model(model_type: type[T_Model], input: bytes) -> T_Model:
    try:
        return model_type.model_validate(bytes_to_json(input))
    except ValidationError as e:
        raise CodeError(model_validation_error) from e

def convert_enums(data: Any) -> Any:
    if isinstance(data, dict):
        new = {}
        for k, v in data.items():
            new[k] = _convert_enums_v(v)
        return new
    elif isinstance(data, (list, tuple, set)):
        r = []
        for x in data:
            r.append(convert_enums(x))
        return r
    else:
        return data

def _convert_enums_v(v: Any) -> Any:
    final_v = v
    if isinstance(v, Enum):
        final_v = v.value
    elif isinstance(v, dict):
        final_v = convert_enums(v)
    elif isinstance(v, (list, tuple, set)):
        final_v = []
        for x in v:
            final_v.append(_convert_enums_v(x))
    return final_v


def bytes_to_string(input: bytes) -> str:
    return input.decode(ENCODING)

def string_to_bytes(input: str) -> bytes:
    return input.encode(ENCODING)


def models_to_bytes(models: Sequence[BaseModel]) -> bytes:
    return json.dumps([x.model_dump() for x in models]).encode(ENCODING)

def model_to_bytes(model: BaseModel) -> bytes:
    return model.model_dump_json().encode(ENCODING)


def json_to_bytes(input: Any) -> bytes:
    return json.dumps(convert_enums(input)).encode(ENCODING)

def bytes_to_json(input: bytes) -> Any:
    if input == bytes():
        return {}
    return json.loads(input.decode(ENCODING))

def float_to_bytes(input: float) -> bytes:
    return struct.pack("<f", input)

def bytes_to_float(input: bytes) -> float:
    return struct.unpack("<f", input)[0]

def int_to_bytes(input: int, size: int, signed: bool) -> bytes:
    return input.to_bytes(size, byteorder="little", signed=signed)

def adaptively_to_bytes(input: Any, signed: bool):
    if isinstance(input, str):
        return string_to_bytes(input)
    elif isinstance(input, int):
        return int_to_bytes(input, 8, signed)
    elif isinstance(input, bytes):
        return input
    else:
        raise TypeError("Unsupported data type")

def unwrap_coded_structure(input: bytes) -> tuple[int, bytes]:
    """
    Unwraps bytes structure consisting of 2 leading bytes of integer code, and rest of the bytes as payload.

    Returns tuple of code and payload.
    """
    if len(input) < 2:
        raise Exception("too short coded structure")
    code = struct.unpack("<H", input[:2])[0]
    payload = bytes()
    if len(input) > 2:
        payload = input[2:]
    return code, payload
