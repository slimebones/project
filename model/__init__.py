from pathlib import Path
from typing import Any, Self
import const
from pydantic import BaseModel

from controller import response
from grand import YeletsGrandContext
import yelets


class Module(BaseModel):
    id: str
    version: str

    @classmethod
    def read(cls, dir: Path) -> Self:
        r = yelets.execute_file(dir)
        return cls(
            id=r["id"],
            version=r["version"],
        )


class Project(BaseModel):
    id: str
    source: Path
    modules: dict[Path, Module]
    context: dict

    @classmethod
    def read(cls, f: Path, target_version, target_debug) -> Self:
        project = cls(
            id="*unknown*",
            source=f.parent,
            modules={},
            context={},
        )
        defines = {
            "grand": YeletsGrandContext(
                response=response,
                project=project,
                cwd=f.parent,
                indentation=const.indentation,
                target_version=target_version,
                target_debug=target_debug,
            ),
        }
        ctx = yelets.execute_file(f, defines)

        project_id = ctx.get("id", "")
        if not isinstance(project_id, str):
            raise Exception(f"Invalid project name at location '{f}'.")
        elif project_id == "":
            raise Exception(f"Empty project name at location '{f}'.")
        elif project_id is None or project_id == "":
            raise Exception(f"Invalid project configuration at '{f}'.")

        modules = ctx.get("modules", {})
        processed_modules = {}
        for k, v in modules.items():
            processed_modules[Path(k)] = Module(
                id=v["id"],
                version=v["version"],
            )

        project.id = project_id
        project.context = ctx
        project.modules = processed_modules

        return project