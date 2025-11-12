"""
Yelets interpreter, Python implementation.

We either panic, or return something meaningful.
"""

import argparse
from yelets import cmd
from os import PathLike
import os
from pathlib import Path
import re
import tarfile
from typing import Any

import call


class Namespace:
    def __init__(self, **kwargs) -> None:
        self._data = kwargs

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        else:
            return self._data[__name]


def to_python(code: str, imports: dict | None = None) -> tuple[str, dict]:
    result = ""
    ind = 0
    preserve_block_close = 0
    globs = {}

    for i, line in enumerate(code.splitlines()):
        linenumber = i + 1
        l = line.strip()
        prefix = "    " * ind

        if l == "}" or l == "},":
            if ind:
                ind -= 1
            prefix = "    " * (ind)
            if preserve_block_close:
                preserve_block_close -= 1
                result += prefix + l + "\n"
            continue

        dict_match = re.match(r"^\s*([A-z0-9_]+)\s*=\s*{\s*$", l)
        if dict_match:
            result += f"{prefix}{dict_match.group(1)} = " + "{\n"
            preserve_block_close += 1
            ind += 1
            continue

        subdict_match = re.match(r"^\s*\"?([A-z0-9_]+)\"?\s*:\s*{\s*$", l)
        if subdict_match:
            result += f"{prefix}\"{subdict_match.group(1)}\":" + " {\n"
            preserve_block_close += 1
            ind += 1
            continue

        subdict_direct_match = re.match(r"^\s*\"?([A-z0-9_]+)\"?\s*:\s*(.+)\s*$", l)
        if subdict_direct_match:
            result += f"{prefix}\"{subdict_direct_match.group(1)}\": {subdict_direct_match.group(2)}\n"
            continue

        function_match = re.match(r"^\s*([A-z0-9_]+)\s*=\s*fn\s*\((.*)\)\s*{\s*$", l)
        if function_match:
            result += f"{prefix}def {function_match.group(1)}({function_match.group(2)}):\n"
            ind += 1
            continue

        # for now, imports act as global namespace update, even if they are executed locally
        import_match = re.match(r"^\s*([A-z0-9_]+)\s*=\s*@import\s*\(\"([A-z0-9_\-\.]+)\"\)\s*$", l)
        if import_match:
            varname = import_match.group(1)
            importname = import_match.group(2)
            if not imports or importname not in imports:
                raise Exception(f"yelets: unrecognized import '{importname}' at line {linenumber}")
            imp = imports[importname]
            globs[varname] = Namespace(**imp)
            continue

        if_match = re.match(r"^\s*if\s*(.+)\s*{\s*$", l)
        if if_match:
            result += f"{prefix}if {if_match.group(1)}:\n"
            ind += 1
            continue

        for_match = re.match(r"^\s*for\s*(.+)\s*{\s*$", l)
        if for_match:
            result += f"{prefix}for {for_match.group(1)}:\n"
            ind += 1
            continue

        while_match = re.match(r"^\s*while\s*(.+)\s*{\s*$", l)
        if while_match:
            result += f"{prefix}while {while_match.group(1)}:\n"
            ind += 1
            continue

        result += prefix + l + "\n"

    return result, globs


# Convert everything to python, and execute as python script.
#
# Returns resulting local namespace.
def execute(code: str, imports: dict | None = None) -> dict:
    if imports is None:
        imports = {}
    builtin_imports = {
        "cmd": cmd.yelets_module,
    }
    final_imports = dict(**builtin_imports, **imports)
    python_code, globs = to_python(code, final_imports)

    locals = {}
    exec(python_code, globs, locals)
    return locals


def execute_file(p: Path, imports: dict | None = None) -> dict:
    with p.open("r") as file:
        code = file.read()
    return execute(code, imports)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("entry", type=Path)
    args = parser.parse_args()
    entry_path = args.entry
    execute_file(entry_path)


if __name__ == "__main__":
    main()
