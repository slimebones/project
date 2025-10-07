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

current_project: Project
projects: dict[str, Project] = {}


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


async def execute_project_function(projectfile: Path, function_name: str):
    yelets_defines = {
        "grand": YeletsGrandContext(
            response=response,
            current_project=current_project,
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

    project = Project(
        id=project_id,
        source=projectfile.parent,
        context=project_context,
    )
    projects[project.id] = project


async def cmd_execute(function_name: str):
    await execute_project_function(Path(cwd, "projectfile"), function_name)


async def cmd_execute_all(function_name: str):
    # Collect projects.
    for source, subdirs, subfiles in cwd.walk():
        for file in subfiles:
            # @todo We should be able to search for `project`, `project.y`, `project.jai`, etc. Project file implementation does not matter as long as we have a driver for it. What matters, is complying to our standards - drivers should execute file in a way, that left us with a namespace map, with converted to python objects, including functions.
            if file == "projectfile":
                config_path = Path(source, file)
                await execute_project_function(config_path, function_name)


    response(f"Collected {len(projects)} projects.", end="\n\n")

    # We remove the whole dir ".build" - noone else should occupy it if we're about to use project utilities at full capacity.
    # Do it at this stage to remove after the projects are collected.
    shutil.rmtree(build_dir)
    global build_time
    build_time = int(time.time() * 1000)

    for i, project in enumerate(projects.values()):
        if i != 0:
            # Separate entries.
            response("")

        response(f"{colorama.Fore.MAGENTA}== BUILD: {project.id} =={colorama.Fore.RESET}")
        response(colorama.Style.DIM, end="")
        build_function = project.context.get("build", None)
        if build_function is None or not callable(build_function):
            response(f"{colorama.Fore.WHITE}{colorama.Style.DIM}No build procedure.{colorama.Fore.RESET}{colorama.Style.RESET_ALL}")
            continue
        global current_project
        current_project = project
        try:
            # @todo Pass some context to custom build functions.
            build_function()
        except Exception as error:
            response(f"{colorama.Fore.RED}ERROR{colorama.Fore.RESET}: Build function of project '{project.id}' panicked with an error: {error}")
            response(f"{colorama.Fore.RED}Build for '{project.id}' failed.{colorama.Fore.RESET}")
        else:
            response(f"{colorama.Fore.GREEN}Build for '{project.id}' finished.{colorama.Fore.RESET}")
        response(colorama.Style.RESET_ALL, end="")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-cwd", type=Path, dest="cwd", default=Path.cwd())
    parser.add_argument("-v, -version", type=str, default="0.0.0")
    parser.add_argument("-d, -debug", action="store_true", dest="debug")

    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # `project execute`
    execute_parser = subparsers.add_parser("execute", help="Executes a function from the cwd's projectfile.")
    execute_parser.add_argument("function_name", type=str)

    # `project execute-all`
    execute_parser = subparsers.add_parser("execute-all", help="Executes a function from the cwd's projectfile and all the subprojects.")
    execute_parser.add_argument("function_name", type=str)

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
            await cmd_execute(args.function_name)
        case "execute-all":
            await cmd_execute_all(args.function_name)
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
