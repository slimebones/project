"""
Client to manage modules.
"""
import io
from pathlib import Path
import shutil
import tarfile
from typing import Callable

from pydantic import BaseModel
import config
import location
import log
import httpx

from model import Project
import xrandom
import yelets

_host: str
_port: int

_projectfile: Path
_target_version: str
_target_debug: bool
_cwd: Path
_response: Callable


def _request(route: str, data: bytes = bytes()) -> httpx.Response:
    return httpx.request("post", f"http://{_host}:{_port}/{route}", content=data)


async def cmd_install():
    project = Project.read(_projectfile, _target_version, _target_debug, _cwd)
    for path, module in project.modules.items():
        # request module tar from the server
        log.info(f"download {module.id}={module.version} to '{path}'")
        response = _request(f"download/@{module.id}={module.version}")

        if response.status_code != 200:
            log.error(f"failed to install module {module}")
            continue

        if path.exists():
            trash_dir = location.user("trash")
            trash_dir.mkdir(parents=True, exist_ok=True)
            trash_path = Path(trash_dir, f"{path.name}_{xrandom.makeid()}")
            log.info(f"move path '{path}' to trash '{trash_path}'")
            shutil.move(path, trash_path)

        # unwrap tar on the fly
        with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
            tar.extractall(path=path)


async def cmd_add(dependency_name: str, dependency_version: str, output_dir: Path | None):
    project = Project.read(_projectfile, _target_version, _target_debug, _cwd)
    # strategy: parse modules, remove old record, insert new modules record at the end of the file
    content = ""
    with _projectfile.open("r") as f:
        inside_modules = False
        for i, line in enumerate(f.readlines()):
            linenumber = i + 1

            if line.strip() == "modules = {":
                inside_modules = True
            elif line.strip() == "}" and inside_modules:
                inside_modules = False
                continue

            if inside_modules:
                continue

            content += line

    content += "\n"

    if output_dir is None:
        output_dir = Path(_cwd, dependency_name)

    # transform from dict[Path, Module] to dict[str, dict]
    modules = {}
    for k, v in project.modules.items():
        modules[k.name] = v.model_dump()

    if output_dir.name in modules:
        modules[output_dir.name]["id"] = dependency_name
        modules[output_dir.name]["version"] = dependency_version
    else:
        modules[output_dir.name] = {
            "id": dependency_name,
            "version": dependency_version,
        }

    def format_dict(d, indent_level=0):
        """Custom function to format a dictionary with indentation and quotes."""
        if not isinstance(d, dict):
            raise ValueError("Input must be a dictionary")

        indent = "    " * indent_level
        indent_minus = "    " * (indent_level-1)
        items = []

        for key, value in d.items():
            # Recursively format nested dictionaries
            formatted_key = f'"{key}"'
            if isinstance(value, dict):
                formatted_value = format_dict(value, indent_level + 1)  # Increase indentation
            else:
                formatted_value = repr(value)
                if formatted_value.startswith("'"):
                    formatted_value = "\"" + formatted_value.removeprefix("'")
                if formatted_value.endswith("'"):
                    formatted_value = formatted_value.removesuffix("'") + "\""

            # Create item string
            items.append(f"{indent}{formatted_key}: {formatted_value}")

        return "{\n" + ",\n".join(items) + f",\n{indent_minus}" + "}"

    formatted_modules = format_dict(modules, 1)
    content += f"modules = {formatted_modules}"
    with _projectfile.open("w") as f:
        f.write(content)


async def cmd_upload(dir: Path):
    data = _compress(dir)
    r = _request("upload", data)
    _response(r.status_code)
    _response(r.text)


def _compress(dir: Path) -> bytes:
    byte_stream = io.BytesIO()
    with tarfile.open(fileobj=byte_stream, mode="w:gz") as tar:
        for item in dir.iterdir():
            tar.add(item, arcname=item.name)
    byte_stream.seek(0)
    return byte_stream.getvalue()


def init(projectfile: Path, target_version: str, target_debug: bool, cwd: Path, response: Callable):
    global _projectfile
    global _target_version
    global _target_debug
    global _cwd
    global _response
    _projectfile = projectfile
    _target_version = target_version
    _target_debug = target_debug
    _cwd = cwd
    _response = response

    global _host
    _host = config.get("module", "host", "81.163.30.25")
    port_str = config.get("module", "port", "9650")

    global _port
    try:
        _port = int(port_str, 10)
    except ValueError as e:
        raise Exception(f"module: configured port should be integer") from e