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
            
            <p><a href="/docs">Interactive API docs</a> | <a href="/ui">Interactive UI</a></p>
        </body>
    </html>
    """


@app.get("/ui", response_class=HTMLResponse)
async def ui():
    """Interactive web UI for the Socratic Tutor."""
    return """
    <html>
        <head>
            <title>Socratic Tutor - Interactive UI</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
                .container { max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
                .header h1 { font-size: 28px; margin-bottom: 10px; }
                .header p { opacity: 0.9; }
                .content { padding: 30px; }
                .section { margin-bottom: 25px; }
                .section-title { font-size: 14px; font-weight: 600; color: #667eea; text-transform: uppercase; margin-bottom: 12px; }
                select, textarea, input { width: 100%; padding: 12px; font-size: 14px; border: 2px solid #e0e0e0; border-radius: 6px; font-family: inherit; }
                select:focus, textarea:focus, input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
                .button-group { display: flex; gap: 10px; }
                button { flex: 1; padding: 12px 20px; font-size: 14px; font-weight: 600; border: none; border-radius: 6px; cursor: pointer; transition: all 0.3s; }
                .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }
                .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
                .output { background: #f8f9fa; border-left: 4px solid #667eea; padding: 16px; border-radius: 6px; margin-bottom: 15px; display: none; }
                .output.show { display: block; }
                .output-label { color: #667eea; font-weight: 600; margin-bottom: 8px; }
                .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
                .metric { background: #f0f4ff; padding: 16px; border-radius: 8px; text-align: center; }
                .metric-value { font-size: 24px; font-weight: bold; color: #667eea; }
                .metric-label { font-size: 12px; color: #666; margin-top: 8px; text-transform: uppercase; }
                .episode-done { display: none; background: #d4edda; border: 2px solid #28a745; padding: 16px; border-radius: 8px; margin: 20px 0; color: #155724; text-align: center; }
                .episode-done.show { display: block; }
                .episode-done-title { font-weight: 600; font-size: 16px; margin-bottom: 8px; }
                .loading { display: none; text-align: center; color: #667eea; }
                .loading.show { display: block; }
                .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #e0e0e0; border-top-color: #667eea; border-radius: 50%; animation: spin 0.6s linear infinite; }
                @keyframes spin { to { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧑‍🏫 Socratic Tutor</h1>
                    <p>Interactive Demo - Teach an AI student through dialogue</p>
                </div>

                <div class="content">
                    <div class="section">
                        <div class="section-title">🎯 Select Task</div>
                        <select id="taskSelect">
                            <option value="easy">Easy - Gravity (Galileo's Falling Objects)</option>
                            <option value="medium">Medium - Electricity (Current Conservation)</option>
                            <option value="hard">Hard - Evolution (Socratic Questions Only)</option>
                        </select>
                        <div class="button-group" style="margin-top: 12px;">
                            <button class="btn-primary" onclick="resetEpisode()">Start New Episode</button>
                        </div>
                    </div>

                    <div class="metrics" id="metrics" style="display: none;">
                        <div class="metric">
                            <div class="metric-value" id="turnCount">0</div>
                            <div class="metric-label">Turn #</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="totalReward">0.00</div>
                            <div class="metric-label">Total Reward</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="beliefScore">0.1</div>
                            <div class="metric-label">Belief Score</div>
                        </div>
                    </div>

                    <div class="output" id="output">
                        <div class="output-label">👨‍🎓 Student Response</div>
                        <p id="studentResponse"></p>
                    </div>

                    <div class="section">
                        <div class="section-title">💬 Your Message</div>
                        <textarea id="teacherMsg" placeholder="Ask a question or provide guidance..." style="height: 100px; resize: vertical;"></textarea>
                        <div class="button-group" style="margin-top: 12px;">
                            <button class="btn-primary" onclick="sendMessage()" id="sendBtn">Send & Get Response</button>
                        </div>
                        <div class="loading" id="loading">
                            <div class="spinner"></div>
                            <p style="margin-top: 10px;">Waiting for student response...</p>
                        </div>
                    </div>

                    <div class="episode-done" id="episodeDone">
                        <div class="episode-done-title">✅ Episode Complete!</div>
                        <div>Final Score: <strong id="finalScoreMsg">-</strong></div>
                    </div>
                </div>
            </div>

            <script>
                async function resetEpisode() {
                    const task = document.getElementById('taskSelect').value;
                    document.getElementById('sendBtn').disabled = true;
                    try {
                        const r = await fetch('/reset', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({task_id: task})
                        });
                        const data = await r.json();
                        updateOutput(data);
                        document.getElementById('metrics').style.display = 'grid';
                        document.getElementById('totalReward').textContent = '0.00';
                        document.getElementById('episodeDone').classList.remove('show');
                        document.getElementById('teacherMsg').value = '';
                    } finally {
                        document.getElementById('sendBtn').disabled = false;
                    }
                }

                async function sendMessage() {
                    const msg = document.getElementById('teacherMsg').value.trim();
                    if (!msg) { alert('Please enter a message'); return; }
                    
                    document.getElementById('sendBtn').disabled = true;
                    document.getElementById('loading').classList.add('show');
                    
                    try {
                        const r = await fetch('/step', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({utterance: msg})
                        });
                        const data = await r.json();
                        updateOutput(data.observation);
                        
                        const prevReward = parseFloat(document.getElementById('totalReward').textContent);
                        document.getElementById('totalReward').textContent = (prevReward + data.reward).toFixed(2);
                        document.getElementById('teacherMsg').value = '';
                        
                        if (data.done) {
                            const score = await (await fetch('/score')).json();
                            document.getElementById('finalScoreMsg').textContent = score.score.toFixed(3);
                            document.getElementById('episodeDone').classList.add('show');
                        }
                    } finally {
                        document.getElementById('sendBtn').disabled = false;
                        document.getElementById('loading').classList.remove('show');
                    }
                }

                function updateOutput(obs) {
                    document.getElementById('output').classList.add('show');
                    document.getElementById('studentResponse').textContent = obs.student_response;
                    document.getElementById('turnCount').textContent = obs.turn_number;
                    document.getElementById('beliefScore').textContent = obs.belief_score.toFixed(3);
                }
            </script>
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


def main():
    """Main entry point for the application."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()