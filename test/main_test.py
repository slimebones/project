from pathlib import Path
import subprocess
from typing import Callable

cwd = Path.cwd()

def call(command: str, dir: Path | str | None = None) -> tuple[str, str, int]:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            cwd=dir,
        )
        return (result.stdout, result.stderr, result.returncode)
    except subprocess.CalledProcessError as e:
        return (e.stdout, e.stderr, e.returncode)

def call_venv(command: str, dir = None):
    return call(f".venv/Scripts/python.exe {Path(cwd, 'main.py')} {command}", dir)

def test_create():
    _, _, e = call_venv("build 0.1.0", "test/data/project_1")
    assert e == 0
    build_dir = Path("test/data/project_1/.build/project_1")
    assert build_dir.exists()
    assert Path(build_dir, "requirements.txt").exists()
    assert Path(build_dir, "build.py").exists()
    assert Path(build_dir, "code.py").exists()
    assert Path(build_dir, "module_a").exists()
    assert Path(build_dir, "module_a/__init__.py").exists()