import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with documentation."""
    return """
    <html>
        <head>
            <title>Socratic Tutor Environment</title>
            <style>
                body { font-family: sans-serif; margin: 40px; }
                h1 { color: #333; }
                code { background: #f4f4f4; padding: 2px 5px; }
                .endpoint { margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>🧑‍🏫 Socratic Tutor Environment</h1>
            <p>An OpenEnv environment for training AI teacher agents using the Socratic method.</p>
            
            <h2>API Endpoints</h2>
            <div class="endpoint">
                <strong>GET /health</strong> - Health check
            </div>
            <div class="endpoint">
                <strong>POST /reset</strong> - Reset episode with optional task_id (easy/medium/hard)
            </div>
            <div class="endpoint">
                <strong>POST /step</strong> - Submit teacher utterance
            </div>
            <div class="endpoint">
                <strong>GET /state</strong> - Get full environment state
            </div>
            <div class="endpoint">
                <strong>GET /score</strong> - Get episode score and metrics
            </div>
            
            <h2>Tasks</h2>
            <ul>
                <li><strong>easy:</strong> Gravity & falling objects (Galileo)</li>
                <li><strong>medium:</strong> Electricity & circuits (current conservation)</li>
                <li><strong>hard:</strong> Evolution (Socratic questions only)</li>
            </ul>
            
            <p><a href="/docs">Interactive API docs</a></p>
        </body>
    </html>
    """


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