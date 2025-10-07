# Project management tool.

import argparse
import asyncio
from call import call
import commit as commitmod
import sys
from typing import Any
from os import PathLike
import colorama
from grand import YeletsGrandContext
import location
from project import Project
import yelets
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Callable, Literal
from pydantic import BaseModel


indentation = " " * 4

red = '\033[31m'
green = '\033[32m'
reset = '\033[0m'
grey = '\033[90m'
# ]]]] nvim fix

# Project is always called in the current working directory. @todo add ability to override cwd via CLI.
cwd = location.cwd()
build_dir: Path
target_debug: bool
target_version: str


async def cmd_status():
    stdout, stderr, e = call("git status")
    if e > 0:
        response(f"project status finished with code #{e}")
    response(stdout, end="")
    response(stderr, end="")


async def cmd_commit():
    commitmod.commit(response)


async def cmd_update():
    stdout, stderr, e = call("git pull")
    if e > 0:
        response(f"project update finished with code #{e}")
    response(stdout, end="")
    response(stderr, end="")


async def cmd_push():
    stdout, stderr, e = call("git push")
    if e > 0:
        response(f"project push finished with code #{e}")
    response(stdout, end="")
    response(stderr, end="")

    stdout, stderr, e = call("git push --tags")
    if e > 0:
        response(f"project push tags finished with code #{e}")
    response(stdout, end="")
    response(stderr, end="")


def response(*messages, end: str = "\n", sep: str = " "):
    print(*messages, file=sys.stderr, end=end, sep=sep)


async def cmd_module():
    pass


async def cmd_template():
    pass


class YeletsFunctionArgs:
    def __init__(self, positional, keyword):
        self.positional = positional
        self.keyword = keyword

    def __getitem__(self, index: int):
        try:
            return self.positional[index]
        except IndexError:
            return None

    def __getattribute__(self, key: str) -> Any:
        return self.keyword.get(key, None)

async def execute_project_function(projectfile: Path, function_name: str, args: YeletsFunctionArgs):
    project = Project(
        id="*unknown*",
        source=projectfile.parent,
    )

    yelets_defines = {
        "grand": YeletsGrandContext(
            response=response,
            project=project,
            cwd=cwd,
            indentation=indentation,
            target_version=target_version,
            target_debug=target_debug,
            build_dir=build_dir,
        ),
    }
    project_context = yelets.execute_file(projectfile, yelets_defines)

    project_id = project_context.get("id", "")
    if not isinstance(project_id, str):
        raise Exception(f"Invalid project name at location '{projectfile}'.")
    elif project_id == "":
        raise Exception(f"Empty project name at location '{projectfile}'.")
    elif project_id is None or project_id == "":
        raise Exception(f"Invalid project configuration at '{projectfile}'.")

    project.id = project_id

    function = project_context.get(function_name, None)
    if function is None:
        raise Exception(f"Could not find a function '{function_name}' at '{projectfile}'.")
    if not callable(function):
        raise Exception(f"Object '{function_name}' at '{projectfile}' expected to be callable.")


async def cmd_execute(function_name: str, args: YeletsFunctionArgs):
    await execute_project_function(Path(cwd, "projectfile"), function_name, args)


async def cmd_execute_all(function_name: str, args: YeletsFunctionArgs):
    # Collect projects.
    for source, subdirs, subfiles in cwd.walk():
        for file in subfiles:
            # @todo We should be able to search for `project`, `project.y`, `project.jai`, etc. Project file implementation does not matter as long as we have a driver for it. What matters, is complying to our standards - drivers should execute file in a way, that left us with a namespace map, with converted to python objects, including functions.
            if file == "projectfile":
                config_path = Path(source, file)
                await execute_project_function(config_path, function_name, args)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-cwd", type=Path, dest="cwd", default=Path.cwd())
    parser.add_argument("-v, -version", type=str, default="0.0.0")
    parser.add_argument("-d, -debug", action="store_true", dest="debug")

    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # `project execute`
    subparser = subparsers.add_parser("execute", help="Executes a function from the cwd's projectfile.")
    subparser.add_argument("function_name", type=str)
    subparser.add_argument("positional", nargs="*", help="Positional arguments to a project's function.")
    subparser.add_argument("--keyword", action="append", nargs=2, metavar=("KEY", "VALUE"), help="Keyword arguments to a project's function.")

    # `project execute-all`
    subparser = subparsers.add_parser("execute-all", help="Executes a function from the cwd's projectfile and all the subprojects.")
    subparser.add_argument("function_name", type=str)
    subparser.add_argument("positional", nargs="*", help="Positional arguments to a project's function.")
    subparser.add_argument("--keyword", action="append", nargs=2, metavar=("KEY", "VALUE"), help="Keyword arguments to a project's function.")

    # `project status`
    subparsers.add_parser("status", help="Show status.")

    # `project commit`
    subparsers.add_parser("commit", help="Commit changes.")

    # `project push`
    subparsers.add_parser("push", help="Push changes.")

    # `project update`
    subparsers.add_parser("update", help="Update from version control.")

    args = parser.parse_args()
    global cwd
    cwd = args.cwd
    global build_dir
    build_dir = Path(cwd, ".build")
    global target_version
    target_version = args.version
    global target_debug
    target_debug = args.debug


    match args.command:
        case "execute":
            args = YeletsFunctionArgs(args.positional, {kv[0]: kv[1] for kv in args.keyword} if args.keyword else {})
            await cmd_execute(args.function_name, args)
        case "execute-all":
            args = YeletsFunctionArgs(args.positional, {kv[0]: kv[1] for kv in args.keyword} if args.keyword else {})
            await cmd_execute_all(args.function_name, args)
        case "module":
            await cmd_module()
        case "template":
            await cmd_template()
        case "status":
            await cmd_status()
        case "commit":
            await cmd_commit()
        case "update":
            await cmd_update()
        case "push":
            await cmd_push()
        case _:
            raise Exception(f"unrecognized command '{args.command}'")


if __name__ == "__main__":
    asyncio.run(main())
