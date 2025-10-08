"""
Client to manage modules.
"""
import os
from pathlib import Path

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


def install(projectfile: Path, target_version: str, target_debug: bool):
    project = Project.read(projectfile, target_version, target_debug)
    for module in project.modules:
        print(module)


def add():
    # for now manual `projectfile::modules` editing should be done
    pass


def upload():
    pass