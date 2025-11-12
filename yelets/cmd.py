"""
Yelets module to provide basic command helper functions.
"""
from os import PathLike
import os
from pathlib import Path
import tarfile
import call as native_call


def tar(source_dir: PathLike, output_filename: PathLike):
    """Create a .tar.gz archive from the specified directory."""
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def untar(tar_gz_path: PathLike, extract_path: PathLike):
    """Extract a .tar.gz archive to the specified directory."""
    with tarfile.open(tar_gz_path, "r:gz") as tar:
        tar.extractall(path=extract_path)


def trash(*paths: PathLike):
    """Universal trash command."""
    call(f"~/.app/trash/trash.py trash {' '.join([str(x) for x in paths])}")


def rm(*paths: PathLike):
    call(f"rm -rf {' '.join([str(x) for x in paths])}")


def call(command: str, dir: Path | str | None = None) -> tuple[str, str, int]:
    return native_call.call(command, dir)


yelets_module = {
    "tar": tar,
    "untar": untar,
    "trash": trash,
    "call": call,
}