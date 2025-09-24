# Yelets interpreter, prototype Python implementation.

import argparse
from pathlib import Path
import re

def panic(message: str):
    raise Exception("PANIC: " + message)

BUILTIN = {
    "panic": panic,
}

def to_python(code: str) -> str:
    result = ""

    for line in code.split("\n"):
        function_match = re.match(r"^([a-z0-9]+) = \(\) {$", line)
        # }
        if function_match:
            result += f"def {function_match.group(1)}():\n"
            continue
        elif line.strip() == "}":
            continue
        line = line.removesuffix(";")
        result += line + "\n"

    return result

# Convert everything to python, and execute as python script.
# 
# Returns resulting local namespace.
def execute(code: str, defines: dict | None = None) -> dict:
    python_code = to_python(code)
    
    globals = {}
    globals.update(BUILTIN)
    if defines:
        globals.update(defines)
    locals = {}
    exec(python_code, globals, locals)
    return locals

def execute_file(p: Path, defines: dict | None = None) -> dict:
    with p.open("r") as file:
        code = file.read()
    return execute(code, defines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("entry", type=Path)
    args = parser.parse_args()
    entry_path = args.entry
    execute_file(entry_path)

if __name__ == "__main__":
    main()
