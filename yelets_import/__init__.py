from os import PathLike
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import TYPE_CHECKING, Callable

import colorama

import xtime

if TYPE_CHECKING:
    from model import Project


_response: Callable
_project: "Project"
_cwd: Path
_indentation: str
_target_version: str
_target_debug: bool
_project_codes: list[str] | None
_codename_rules: str
_build_dir: Path


def init(*, response: Callable, project: "Project", cwd: Path, indentation: str, target_version: str, target_debug: bool):
    global _response
    global _project
    global _cwd
    global _indentation
    global _target_version
    global _target_debug
    global _project_codes
    global _codename_rules
    global _build_dir

    _response = response
    _project = project
    _project_codes = None
    _cwd = cwd
    _codename_rules = """{ind}1. alphanumeric
{ind}2. lower case
{ind}3. separated by underscores
{ind}4. not starting with an underscore
{ind}5. not ending with an underscore
{ind}6. not starting with a digit"""
    _indentation = indentation
    _target_debug = target_debug
    _build_dir = Path(project.source, ".build")

    # We recreate whole build dir - noone else should occupy it if we're about to use project utilities at full capacity.
    if _build_dir.exists():
        shutil.rmtree(_build_dir)
    _build_dir.mkdir(parents=True, exist_ok=True)

    # Setup version.
    major, minor, patch = target_version.removeprefix("v").split(".")
    major = int(major)
    minor = int(minor)
    patch = int(patch)
    if major < 0 or minor < 0 or patch < 0:
        raise Exception("Wrong version setup. Expected 'major.minor.patch' format.")
    _target_version = f"{major}.{minor}.{patch}"


def call(command: str, callback: Callable[[int, str], None] | None = None):
    # Always call relatively to the current project.
    loc = _project.source

    # Use nushell command.
    if "\"" in command:
        _response(f"{colorama.Fore.YELLOW}WARNING{colorama.Fore.RESET}: Please, do not use double-quotes for 'call' commands - they will be replaced with single-quotes. Occurred for project '{_project.id}', command: {command}")
        command = command.replace("\"", "'")
    command = f"nu -c \"{command}\""

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=loc,
        bufsize=1,
        universal_newlines=True,
    )
    # @todo Make it parallel, somehow. For now it is printed only at the end of the subprocess. At least this behaviour is noticed at Windows.
    if callback is not None:
        if process.stdout is not None:
            for line in process.stdout:
                callback(1, line)
        if process.stderr is not None:
            for line in process.stderr:
                callback(2, line)
    code = process.wait()
    if code != 0:
        raise Exception(f"Call returned code {code}, location '{loc}', command: {command}")

def code(target: PathLike):
    """
    Build a codesheet, writing to given `target`.

    Built codesheet includes a programming-language-specific compile-time (or boot-time) constant definitions, and a dictionary-like definition, where the keys are codes, and the values are codenames.
    """
    global _project_codes
    if _project_codes is None:
        _project_codes = []
        # note that we always search `code.txt` under the current working directory
        code_path = Path(_cwd, "code.txt")
        if code_path.exists():
            with code_path.open("r") as file:
                lines = file.readlines()
                for line in lines:
                    line = line.strip().lower()
                    # Codes must be parsed strictly. We want our `codes.txt` file to look clean.
                    # We add even empty lines - codes must be correctly enumerated. Later empty lines will be replaced by empty lines during code-file generation.
                    if line:
                        if line in ["ok", "codenames"]:
                            raise Exception(f"Cannot use reserved codename '{line}'.")
                        if not re.match(r"^(?![0-9])(?<!_)([a-z0-9]+(?:_[a-z0-9]+)*)[^_]$", line):
                            raise Exception(f"Invalid codename: '{line}'. Codename rules:\n{_codename_rules.format(ind=_indentation)}")
                        if line in _project_codes:
                            raise Exception(f"Duplicate definition of a codename '{line}'.")

                    _project_codes.append(line)

    _response(f"Generate codes to '{target}'.")
    target = Path(_project.source, target)
    extension = target.suffix.removeprefix(".")
    content = ""
    codenames = ""
    # Codes must be already valid at this point.
    if extension == "py":
        content += "ok = 0\n"
        for code, codename in enumerate(_project_codes):
            code += 1
            content += f"{codename} = {code}\n"
            codenames += f"{_indentation}{code}: \"{codename}\",\n"

        content += """
codenames: dict[int, str] = {{
{codenames}}}""".format(codenames=codenames)

    elif extension in ["js", "ts"]:
        content += "export const ok = 0;\n"
        for code, codename in enumerate(_project_codes):
            code += 1
            content += f"export const {codename} = {code};\n"
            codenames += f"{_indentation}{code}: \"{codename}\",\n"

        content += """
export const codenames = {{
{codenames}}};""".format(codenames=codenames)

    else:
        raise Exception(f"Unsupported codes extension '{extension}' at location '{target}'.")
    with target.open("w+") as f:
        f.write(content)


def includePython():
    for root, dirs, files in os.walk(_project.source):
        if Path(root) == _project.source:
            for filename in files:
                # include requirements and all python filenames
                if filename in "requirements.txt" or filename.endswith(".py"):
                    include(filename)
        # search only top-level modules to include
        elif Path(root).parent == _project.source:
            for filename in files:
                if filename == "__init__.py":
                    include(Path(root).name)


def info(target: PathLike):
    build_timestamp = xtime.timestamp()

    _response(f"Generate build info to '{target}'.")
    target = Path(_project.source, target)
    extension = target.suffix.removeprefix(".")
    auto_message = "AUTO-GENERATED BY THE BUILD SYSTEM. DO NOT EDIT!"
    content = ""
    if extension == "py":
        content = f"# {auto_message}\nproject_id = \"{_project.id}\"\nversion = \"{_target_version}\"\ntimestamp = {build_timestamp}\ndebug = {'True' if _target_debug else 'False'}"
    elif extension in ["js", "ts"]:
        BRACKET_LEFT = "{"
        BRACKET_RIGHT = "}"
        content = f"// {auto_message}\nconst project_id = \"{_project.id}\";\nconst version = \"{_target_version}\";\nconst timestamp = {build_timestamp};\nconst debug = {'true' if _target_debug else 'false'};\nexport {BRACKET_LEFT} project_id, version, timestamp, debug {BRACKET_RIGHT};\n"
    else:
        raise Exception(f"Unsupported build info extension '{extension}' at location '{target}'.")
    with target.open("w+") as f:
        f.write(content)


# @todo we also need to use glob as target, like `buildInclude("*.html")`, but in such a case we should disallow `dest`
def include(target: Path | str, dest: Path | str | None = None):
    """
    Includes target into a build directory.
    """
    target = Path(target)
    real_target = Path(_project.source, target)

    message = f"Include target '{target}'."
    if dest:
        message += f" Destination is altered to '{dest}'."
    _response(message)

    if not real_target.exists():
        raise Exception(f"Cannot find include path '{real_target}'.")
    elif real_target.is_dir():
        if dest == ".":
            # We cannot just copytree, or an "already-existing" error will be raised. Instead, we will copy everything from the target directory to the build directory.
            for item in os.listdir(real_target):
                item_path = Path(real_target, item)
                dest_path = Path(_build_dir, item)
                if item_path.is_dir():
                    shutil.copytree(item_path, dest_path)
                else:
                    shutil.copy2(item_path, dest_path)
        else:
            shutil.copytree(real_target, Path(_build_dir, dest if dest else target))
    else:
        if dest == ".":
            raise Exception(f"Include destination of '.' is not allowed for files.")
        shutil.copy2(real_target, Path(_build_dir, dest if dest else target))


imp = {
    "info": info,
    "code": code,
    "call": call,
    "includePython": includePython,
    "include": include,
}