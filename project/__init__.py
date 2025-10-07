from pathlib import Path
from typing import Any
from pydantic import BaseModel


class Project(BaseModel):
    source: Path
    id: str
    context: dict[str, Any]