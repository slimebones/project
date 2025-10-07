from pydantic import BaseModel

class Check(BaseModel):
    a: int
    b: str