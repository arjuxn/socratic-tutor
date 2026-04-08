from typing import List, Optional
from pydantic import BaseModel, Field

class SocraticAction(BaseModel):
    utterance: str = Field(..., min_length=1, max_length=1000)

class SocraticObservation(BaseModel):
    student_response: str
    belief_score: float = Field(..., ge=0.0, le=1.0)
    probe_result: Optional[float] = Field(None, ge=0.0, le=1.0)
    turn_number: int
    done: bool
    task_id: str
    feedback: str = ""

class SocraticState(BaseModel):
    task_id: str
    turn_number: int
    belief_score: float
    transcript: List[dict]
    misconception: str
    correct_answer: str
    done: bool
    total_reward: float