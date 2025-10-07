from pathlib import Path
from typing import Any
from pydantic import BaseModel


class Project(BaseModel):
    id: str
    source: Path