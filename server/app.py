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
            <title>Socratic Tutor</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                html, body { height: 100%; overflow: hidden; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #0a0e27;
                    color: #e0e0e0;
                }
                .container {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    height: 100vh;
                }
                .left {
                    background: #0a0e27;
                    padding: 60px 50px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                .right {
                    background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
                    padding: 60px 50px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    position: relative;
                    overflow: hidden;
                }
                .logo {
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 60px;
                    letter-spacing: 1px;
                    color: #ffffff;
                }
                h1 {
                    font-size: 46px;
                    font-weight: 700;
                    margin-bottom: 20px;
                    color: #ffffff;
                    line-height: 1.2;
                }
                .subtitle {
                    font-size: 16px;
                    color: #888;
                    margin-bottom: 50px;
                    line-height: 1.6;
                }
                .form-group {
                    margin-bottom: 24px;
                }
                .form-label {
                    display: block;
                    font-size: 13px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    color: #777;
                    margin-bottom: 10px;
                }
                select, textarea {
                    width: 100%;
                    padding: 14px 16px;
                    background: #1a1f3a;
                    border: 1px solid #2a3050;
                    color: #e0e0e0;
                    border-radius: 6px;
                    font-size: 15px;
                    font-family: inherit;
                    transition: all 0.3s;
                }
                select option {
                    background: #1a1f3a;
                    color: #e0e0e0;
                }
                select:hover, textarea:hover {
                    border-color: #3a4060;
                }
                select:focus, textarea:focus {
                    outline: none;
                    border-color: #4CAF50;
                    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
                }
                button {
                    width: 100%;
                    padding: 14px 16px;
                    background: #4CAF50;
                    color: #1a1f3a;
                    border: none;
                    border-radius: 6px;
                    font-size: 15px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                button:hover {
                    background: #45a049;
                    transform: translateY(-1px);
                }
                button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    transform: none;
                }
                .stats {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 16px;
                    margin-bottom: 50px;
                    display: none;
                }
                .stats.show {
                    display: grid;
                }
                .stat {
                    background: #1a1f3a;
                    padding: 18px;
                    border-radius: 6px;
                    border: 1px solid #2a3050;
                    text-align: center;
                }
                .stat-value {
                    font-size: 28px;
                    font-weight: 700;
                    color: #4CAF50;
                    margin-bottom: 6px;
                }
                .stat-label {
                    font-size: 12px;
                    color: #888;
                    text-transform: uppercase;
                    letter-spacing: 0.3px;
                }
                .chat-box {
                    background: #1a1f3a;
                    border: 1px solid #2a3050;
                    border-radius: 6px;
                    padding: 24px;
                    margin-bottom: 30px;
                    min-height: 200px;
                    max-height: 400px;
                    overflow-y: auto;
                    display: none;
                }
                .chat-box.show {
                    display: block;
                }
                .message {
                    margin-bottom: 20px;
                }
                .message-label {
                    font-size: 11px;
                    font-weight: 600;
                    text-transform: uppercase;
                    color: #888;
                    margin-bottom: 6px;
                    letter-spacing: 0.3px;
                }
                .message-text {
                    color: #e0e0e0;
                    line-height: 1.6;
                    padding: 12px;
                    background: #0a0e27;
                    border-radius: 4px;
                }
                .loading {
                    display: none;
                    text-align: center;
                    color: #888;
                    margin-bottom: 20px;
                }
                .loading.show {
                    display: block;
                }
                .pulse {
                    display: inline-block;
                }
                .dot {
                    display: inline-block;
                    width: 6px;
                    height: 6px;
                    margin: 0 3px;
                    background: #4CAF50;
                    border-radius: 50%;
                    animation: pulse-dot 1.4s infinite;
                }
                .dot:nth-child(2) { animation-delay: 0.2s; }
                .dot:nth-child(3) { animation-delay: 0.4s; }
                @keyframes pulse-dot {
                    0%, 80%, 100% { opacity: 0.3; }
                    40% { opacity: 1; }
                }
                .completion {
                    display: none;
                    background: #1a1f3a;
                    border: 1px solid #2a3050;
                    border-radius: 6px;
                    padding: 24px;
                    text-align: center;
                    margin-bottom: 30px;
                }
                .completion.show {
                    display: block;
                }
                .completion-msg {
                    color: #4CAF50;
                    font-weight: 600;
                    margin-bottom: 12px;
                }
                .completion-score {
                    font-size: 32px;
                    font-weight: 700;
                    color: #4CAF50;
                }
                .right-content {
                    text-align: center;
                    max-width: 400px;
                }
                .icon-box {
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 30px;
                    background: #ffffff;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                }
                .geo-shape {
                    width: 50px;
                    height: 50px;
                    position: relative;
                }
                .geo-cube {
                    width: 100%;
                    height: 100%;
                    border: 2px solid #4CAF50;
                    transform: perspective(500px) rotateX(20deg) rotateY(-20deg);
                    border-radius: 4px;
                }
                .right-title {
                    font-size: 42px;
                    font-weight: 700;
                    color: #0a0e27;
                    margin-bottom: 16px;
                    line-height: 1.2;
                }
                .right-text {
                    font-size: 15px;
                    color: #666;
                    margin-bottom: 40px;
                    line-height: 1.7;
                }
                .features {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                    margin-top: 50px;
                }
                .feature {
                    text-align: center;
                }
                .feature-icon {
                    font-size: 24px;
                    margin-bottom: 12px;
                    color: #4CAF50;
                }
                .feature-text {
                    font-size: 13px;
                    color: #666;
                }
                ::-webkit-scrollbar {
                    width: 6px;
                }
                ::-webkit-scrollbar-track {
                    background: #1a1f3a;
                }
                ::-webkit-scrollbar-thumb {
                    background: #2a3050;
                    border-radius: 3px;
                }
                ::-webkit-scrollbar-thumb:hover {
                    background: #3a4060;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Left Column -->
                <div class="left">
                    <div class="logo">Socratic</div>
                    <h1>Learn Through Dialogue</h1>
                    <p class="subtitle">Engage with an interactive tutor that challenges your understanding through thoughtful questioning.</p>

                    <div class="form-group">
                        <label class="form-label">Difficulty Level</label>
                        <select id="taskSelect">
                            <option value="easy">Gravity - Elementary</option>
                            <option value="medium">Electricity - Intermediate</option>
                            <option value="hard">Evolution - Advanced</option>
                        </select>
                    </div>

                    <button onclick="resetEpisode()">Start Session</button>

                    <div class="stats" id="stats">
                        <div class="stat">
                            <div class="stat-value" id="turnCount">0</div>
                            <div class="stat-label">Turn</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="totalReward">0.00</div>
                            <div class="stat-label">Progress</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="beliefScore">10%</div>
                            <div class="stat-label">Understanding</div>
                        </div>
                    </div>

                    <div class="chat-box" id="chatBox">
                        <div class="message">
                            <div class="message-label">Instructor</div>
                            <div class="message-text" id="studentResponse"></div>
                        </div>
                    </div>

                    <div class="completion" id="completion">
                        <div class="completion-msg">Session Complete</div>
                        <div class="completion-score" id="finalScore">—</div>
                    </div>

                    <div class="loading" id="loading">
                        <span>Thinking</span><span class="pulse"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Your Response</label>
                        <textarea id="teacherMsg" placeholder="Type your response..."></textarea>
                    </div>

                    <button onclick="sendMessage()" id="sendBtn">Send</button>
                </div>

                <!-- Right Column -->
                <div class="right">
                    <div class="right-content">
                        <div class="icon-box">
                            <div class="geo-shape">
                                <div class="geo-cube"></div>
                            </div>
                        </div>
                        <div class="right-title">Socratic Learning</div>
                        <p class="right-text">Master concepts through guided dialogue. Challenge assumptions and develop deeper understanding.</p>
                        
                        <div class="features">
                            <div class="feature">
                                <div class="feature-icon">▧</div>
                                <div class="feature-text">Adaptive Difficulty</div>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">⚡</div>
                                <div class="feature-text">Real-time Feedback</div>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">◆</div>
                                <div class="feature-text">Progress Tracking</div>
                            </div>
                        </div>
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
                        document.getElementById('stats').classList.add('show');
                        document.getElementById('chatBox').classList.add('show');
                        document.getElementById('totalReward').textContent = '0.00';
                        document.getElementById('completion').classList.remove('show');
                        document.getElementById('teacherMsg').value = '';
                    } finally {
                        document.getElementById('sendBtn').disabled = false;
                    }
                }

                async function sendMessage() {
                    const msg = document.getElementById('teacherMsg').value.trim();
                    if (!msg) return;
                    
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
                            document.getElementById('finalScore').textContent = Math.round(score.score * 100) + '%';
                            document.getElementById('completion').classList.add('show');
                        }
                    } finally {
                        document.getElementById('sendBtn').disabled = false;
                        document.getElementById('loading').classList.remove('show');
                    }
                }

                function updateOutput(obs) {
                    document.getElementById('studentResponse').textContent = obs.student_response;
                    document.getElementById('turnCount').textContent = obs.turn_number;
                    document.getElementById('beliefScore').textContent = Math.round(obs.belief_score * 100) + '%';
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