from pathlib import Path
import subprocess


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