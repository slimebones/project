import subprocess
from pathlib import Path
import re
from typing import Callable

git_files_cmd = "git ls-files --other --modified --exclude-standard"
git_commit_cmd = "git add . && git commit -m \"{0}\""
git_title_core = "Update {0}"
git_title_extra_limit = 50
ansi_red = "\033[31m"
ansi_reset = "\033[0m"

def merge_consecutive_spaces(text):
    return re.sub(r"[ \t]+", " ", text)

def call(command: str) -> tuple[str, int]:
    process = subprocess.run(command, shell=True, text=True, capture_output=True)
    if process.returncode == 0:
        return process.stdout, 0
    else:
        return process.stderr, 1

def commit(response_function: Callable):
    # Check if any of non-gitignored files contain unescaped '@nocommit'. @ignore
    # Note that only cwd-child files are inspected, and we don't inspect all git root -
    # this is logical, since we commit only the cwd's files.
    grep, e = call("git grep @nocommit")  # @ignore
    print(grep)
    # `git grep` returns error if search was unsuccessful, so we treat error positively.
    if e == 0:
        grep_lines = grep.splitlines()
        for line in grep_lines:
            if "@ignore" not in line:
                merged = merge_consecutive_spaces(line).strip()
                response_function(f"{ansi_red}CANNOT COMMIT{ansi_reset}: tag '@nocommit' found in context (spaces merged):\n\t'{merged}'")  # @ignore
                response_function("To ignore: place '@ignore' tag on the same line as '@nocommit'.")
                exit(1)

    p = subprocess.run(git_files_cmd, shell=True, text=True, stdout=subprocess.PIPE)
    if p.returncode > 0:
        response_function(f"'git ls-files' process returned code {p.returncode}, error content is: {p.stderr}")
        exit(p.returncode)
    stdout = p.stdout
    if stdout == "":
        response_function("Nothing to commit.")
        exit(1)

    raw_names = list(filter(
        lambda l: l and not l.isspace(), stdout.split("\n")))
    # collect filenames, put them up until limit is reached
    extra = ""
    names = [raw_name.split("/")[-1] for raw_name in raw_names]
    names_len = len(names)
    for i, name in enumerate(names):
        fname = name
        # not last name receive comma
        if i + 1 < names_len:
            fname += ", "
        if len(extra) + len(name) >= git_title_extra_limit:
            extra += "..."
            break
        extra += fname

    core = git_title_core.format(extra)

    if not core or core.isspace() or names_len == 0:
        response_function(
            "Failed to find commited files info in git ls files stdout:"
            f" {stdout}")
        exit(1)

    p = subprocess.run(
        git_commit_cmd.format(core),
        shell=True,
        text=True,
        stdout=subprocess.PIPE)
    if p.returncode > 0:
        response_function(
            f"Failed to commit: git returned code {p.returncode},"
            f" err content is: {p.stderr}")
        exit(p.returncode)
    response_function(f"Commited {len(raw_names)} entries with message \"{core}\"")
