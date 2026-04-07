from pydantic import BaseModel, Field
from typing import List, Optional

class MyEnvAction(BaseModel):
    message: str = Field(
        ..., 
        description="The command to execute in the environment. Must start with GOTO:, CLICK:, or FINAL:.",
        examples=["GOTO: https://example.com", "FINAL: 1992"]
    )

class MyEnvObservation(BaseModel):
    echoed_message: str = Field(..., description="The textual observation from the browser environment.")

class MyEnvState(BaseModel):
    step_count: int = Field(..., ge=0, description="The number of steps taken in the current episode.")
    history: List[str] = Field(default_factory=list, description="A history of actions taken.")
