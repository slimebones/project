"""
Client to manage modules.
"""
import io
import os
from pathlib import Path
import tarfile

from pydantic import BaseModel
import config
import log
import httpx

from model import Project
import yelets

host: str
port: int

def init():
    global host
    host = config.get("module", "server_host", "81.163.30.25")
    port_str = config.get("module", "server_port", "9650")

    global port
    try:
        port = int(port_str, 10)
    except ValueError as e:
        raise Exception(f"module: configured port should be integer") from e


def _request(route: str, data: bytes = bytes()) -> httpx.Response:
    return httpx.request("post", f"http://{host}:{port}/{route}", content=data)


def install(projectfile: Path, target_version: str, target_debug: bool, cwd: Path):
    project = Project.read(projectfile, target_version, target_debug, cwd)
    for path, module in project.modules.items():
        if path.exists():
            pass
        else:
            # request module tar from the server
            response = _request(f"download/@{module.id}={module.version}")
            # unwrap tar on the fly
            with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
                tar.extractall(path=path)


def add():
    # for now manual `projectfile::modules` editing should be done
    pass


def upload():
    pass


def _compress(dir: Path) -> bytes:
    byte_stream = io.BytesIO()
    with tarfile.open(fileobj=byte_stream, mode="w:gz") as tar:
        for item in dir.iterdir():
            tar.add(item, arcname=item.name)
    byte_stream.seek(0)
    return byte_stream.getvalue()