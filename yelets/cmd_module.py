"""
Yelets module to provide basic command helper functions.
"""
from os import PathLike
import os
from pathlib import Path
import tarfile
import call as native_call
import yelets_project


def tar(source_dir: PathLike, output_filename: PathLike):
    """Create a .tar.gz archive from the specified directory."""
    with tarfile.open(Path(yelets_project.get_project().source, output_filename), "w:gz") as tar:
        tar.add(Path(yelets_project.get_project().source, Path(yelets_project.get_project().source, source_dir)), arcname=os.path.basename(source_dir))


def untar(tar_gz_path: PathLike, extract_path: PathLike):
    """Extract a .tar.gz archive to the specified directory."""
    with tarfile.open(Path(yelets_project.get_project().source, tar_gz_path), "r:gz") as tar:
        tar.extractall(path=Path(yelets_project.get_project().source, extract_path))


def trash(*paths: PathLike):
    """Universal trash command."""
    new_paths = []
    for p in paths:
        new_paths.append(Path(yelets_project.get_project().source, p))
    call(f"~/.app/trash/trash.py trash {' '.join([str(x) for x in new_paths])}", yelets_project.get_project().source)


def rm(*paths: PathLike):
    new_paths = []
    for p in paths:
        new_paths.append(Path(yelets_project.get_project().source, p))
    call(f"rm -rf {' '.join([str(x) for x in new_paths])}", yelets_project.get_project().source)


def call(command: str, dir: Path | str | None = None) -> tuple[str, str, int]:
    if dir is None:
        d = yelets_project.get_project().source
    else:
        d = Path(yelets_project.get_project().source, dir)
    return native_call.call(command, d)


def mustCall(command: str, dir: Path | str | None = None):
    _, stderr, retcode = call(command, dir)
    if retcode != 0:
        raise Exception(f"During call of command '{command}', an error occurred: {stderr}")


mod = {
    "tar": tar,
    "untar": untar,
    "trash": trash,
    "call": call,
    "mustCall": mustCall,
}