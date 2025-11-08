# Project management tool.

import build

import location
location.init(build.project_id)

import log
log.init()

import config
config.init()

import xtime
xtime.init()

import argparse
import asyncio
import functools
import inspect
from call import call
import commit as commitmod
import const
import sys
from typing import Any
from os import PathLike
import colorama
from controller import response
import location
from model import Module, Project
import module
import yelets
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Callable, Literal
from pydantic import BaseModel

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


class YeletsFunctionArgs:
    def __init__(self, positional, keyword):
        self._positional = positional
        for k in keyword.keys():
            if k.startswith("_"):
                raise Exception(f"Keywords are prohibited to start with an underscore.")
        self._keyword = keyword

    def __getitem__(self, index: int):
        try:
            return self._positional[index]
        except IndexError:
            return None

    def __getattribute__(self, key: str) -> Any:
        if key.startswith("_"):
            return super().__getattribute__(key)
        else:
            return self.keyword.get(key, None)


async def execute_project_function(projectfile: Path, function_name: str, args: YeletsFunctionArgs):
    project = Project.read(projectfile, target_version=target_version, target_debug=target_debug, cwd=cwd)

    response(f"{colorama.Fore.MAGENTA}== {colorama.Fore.YELLOW}{project.id}{colorama.Fore.RESET}: {colorama.Fore.CYAN}{function_name}{colorama.Fore.RESET} {colorama.Fore.MAGENTA}=={colorama.Fore.RESET}")

    function = project.context.get(function_name, None)
    if function is None:
        raise Exception(f"Could not find a function '{function_name}' at '{projectfile}'.")
    if not callable(function):
        raise Exception(f"Object '{function_name}' at '{projectfile}' expected to be callable.")

    argument_count = len(inspect.signature(function).parameters)
    final_function = None
    if argument_count == 1:
        final_function = functools.partial(function, args)
    elif argument_count > 1:
        raise Exception(f"Function '{function_name}' at '{projectfile}' should accept zero or one arguments.")
    else:
        final_function = function

    try:
        final_function()
    except Exception as e:
        response(f"{colorama.Fore.RED}ERROR{colorama.Fore.RESET}")
        raise Exception(f"During execution of a function '{function_name}' at '{projectfile}', an error occurred: {e}") from e
    else:
        response(f"{colorama.Fore.GREEN}DONE{colorama.Fore.RESET}")


async def cmd_execute(function_name: str, args: YeletsFunctionArgs):
    await execute_project_function(Path(cwd, "projectfile"), function_name, args)


async def cmd_execute_all(function_name: str, args: YeletsFunctionArgs):
    i = 0
    # Collect projects.
    for source, subdirs, subfiles in cwd.walk():
        for file in subfiles:
            # @todo We should be able to search for `project`, `project.y`, `project.jai`, etc. Project file implementation does not matter as long as we have a driver for it. What matters, is complying to our standards - drivers should execute file in a way, that left us with a namespace map, with converted to python objects, including functions.
            if file == "projectfile":
                projectfile = Path(source, file)
                if i > 0:
                    response()
                await execute_project_function(projectfile, function_name, args)
                i += 1


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-cwd", type=Path, dest="cwd", default=Path.cwd())
    parser.add_argument("-v, -version", type=str, default="0.0.0", dest="version")
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
    subparser.add_argument("-kw", action="append", nargs=2, metavar=("KEY", "VALUE"), help="Keyword arguments to a project's function.")

    # `project install`
    subparsers.add_parser("install", help="Installs/Refreshes all project-specified dependencies.")

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

    try:
        args_kw = args.kw
    except Exception:
        args_kw = {}

    if args_kw is None:
        args_kw = {}

    projectfile = Path(cwd, "projectfile")
    response()
    match args.command:
        case "execute":
            yelets_args = YeletsFunctionArgs(args.positional, {kv[0]: kv[1] for kv in args_kw})
            await cmd_execute(args.function_name, yelets_args)
        case "execute-all":
            yelets_args = YeletsFunctionArgs(args.positional, {kv[0]: kv[1] for kv in args_kw})
            await cmd_execute_all(args.function_name, yelets_args)
        case "install":
            module.install(projectfile, target_version, target_debug, cwd)
        case "template":
            pass
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
    response()


if __name__ == "__main__":
    asyncio.run(main())
