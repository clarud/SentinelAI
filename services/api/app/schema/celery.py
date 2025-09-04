from pydantic import BaseModel

class CeleryResponse(BaseModel):
    task_id: str
    method: list
    arguments: dict

class CeleryTaskResponse(BaseModel):
    state: str
    result: dict