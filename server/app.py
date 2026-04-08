import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from models import SocraticAction
from server.environment import SocraticEnvironment

app = FastAPI(title="Socratic Tutor Environment", version="1.0.0")
_env = SocraticEnvironment()


class ResetRequest(BaseModel):
    task_id: Optional[str] = "easy"

class StepRequest(BaseModel):
    utterance: str


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/reset")
async def reset(request: ResetRequest = None):
    task_id = (request.task_id if request else None) or "easy"
    obs = _env.reset(task_id=task_id)
    return obs.model_dump()

@app.post("/step")
async def step(request: StepRequest):
    action = SocraticAction(utterance=request.utterance)
    obs, reward, done, info = _env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": round(reward, 4),
        "done": done,
        "info": info,
    }

@app.get("/state")
async def state():
    return _env.state().model_dump()

@app.get("/score")
async def score():
    return {
        "score": _env.final_score(),
        "total_reward": round(_env.total_reward, 4),
        "turn_number": _env.turn_number,
        "done": _env.done,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)