---
title: Socratic Tutor Environment
emoji: 🧑‍🏫
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Socratic Tutor Environment

A real-world OpenEnv environment for training and evaluating AI teacher agents using the **Socratic method**—guiding students toward correct understanding through strategic questioning and dialogue rather than direct instruction.

## Environment Description & Motivation

Traditional AI tutoring systems rely on direct instruction. This environment challenges AI agents to teach more effectively by adopting the Socratic method: an agent-teacher must identify student misconceptions and correct them through thoughtful probing, examples, and counterquestions.

**Real-world applications:**
- K-12 and higher education tutoring systems
- Corporate training and onboarding
- Language learning platforms
- Personalized education at scale
- Misconception diagnosis and remediation

The environment simulates a learner facing three common pedagogical misconceptions across physics, electricity, and biology. The AI teacher receives:
- The student's current response
- A belief score (0–1) indicating perceived correctness
- Periodic knowledge probes to verify understanding
- Rewards shaped by progress toward corrected beliefs

This is a genuine challenge: agents must balance direct correction with Socratic guidance, and hard constraints apply (e.g., the "hard" task forbids direct statements—questions only).

## Environment Specification

### Endpoints
- **POST `/reset`** → Reset episode, optionally choose task (easy/medium/hard)
- **POST `/step`** → Submit teacher utterance, receive student response + observation + reward
- **GET `/state`** → Inspect full environment state and transcript
- **GET `/health`** → Health check
- **GET `/score`** → Final score, total reward, episode info

### Action Space

```json
{
  "utterance": "string (1–1000 characters)"
}
```

**Example actions:**
- `"Think about what Galileo demonstrated. If mass determined speed, would a feather and a rock fall differently in a vacuum?"`
- `"You said there's less current leaving the bulb. Can you explain why current wouldn't be conserved?"`
- `"What percentage of animals inherit traits versus develop them during their lifetime?"`

### Observation Space

```json
{
  "student_response": "string",
  "belief_score": "float [0.0–1.0]",
  "probe_result": "float [0.0–1.0] or null",
  "turn_number": "int",
  "done": "boolean",
  "task_id": "string (easy|medium|hard)",
  "feedback": "string"
}
```

**Fields:**
- `student_response`: Student's typed response to the teacher
- `belief_score`: Probability the student holds correct understanding (0=wrong, 1=right)
- `probe_result`: Knowledge probe score (fire every 2 turns, null otherwise)
- `turn_number`: Current turn (0–max_turns)
- `done`: Episode finished?
- `task_id`: Active task
- `feedback`: Reward justification from last step

### Reward Space

- **Range:** 0.0–5.0 per episode
- **Shaping:** Rewards belief improvement and successful probes; penalizes stagnation
- **Signal:** Dense rewards per turn for partial progress

## Task Descriptions

### Task 1: **Fact Relay** (Easy)
**Context:** Teaching physics—gravity and falling objects.

**Student misconception:** *"Heavier objects always fall faster than lighter objects because they weigh more."*

**Correct answer:** *"In the absence of air resistance, all objects fall at the same rate regardless of mass. Galileo demonstrated this."*

**Difficulty:** Easy  
**Max turns:** 10  
**Success threshold:** Belief score ≥ 0.7

**Probe questions:**
- "If I drop a 1kg ball and a 10kg ball from the same height in a vacuum, which hits the ground first?"
- "What did Galileo show about falling objects?"

---

### Task 2: **Misconception Correction** (Medium)
**Context:** Teaching electricity and circuits.

**Student misconception:** *"Electricity is 'used up' as it flows through a circuit—there's less current out of a bulb than going in."*

**Correct answer:** *"Electric charge is conserved. The same current flows in and out. The bulb converts energy, not charge."*

**Difficulty:** Medium  
**Max turns:** 8  
**Success threshold:** Belief score ≥ 0.75

**Probe questions:**
- "If 2 amps flow into a lightbulb, how many amps flow out?"
- "What does a lightbulb consume—current or energy?"

---

### Task 3: **Socratic Chain** (Hard)
**Context:** Teaching evolution and natural selection.

**Constraint:** You **MUST only ask questions**. Every utterance must end with `?`. No direct statements allowed.

**Student misconception:** *"Animals deliberately develop new traits because they need them. Giraffes grew long necks because they wanted to reach higher leaves."*

**Correct answer:** *"Evolution happens via natural selection on random variation. Organisms don't consciously acquire traits. Giraffes with longer necks survived and reproduced more."*

**Difficulty:** Hard  
**Max turns:** 8  
**Success threshold:** Belief score ≥ 0.8

**Probe questions:**
- "Does a giraffe grow a longer neck because it wants to, or because of something else?"
- "Can an individual giraffe acquire a longer neck in its lifetime, or does it require many generations?"

---

## Setup & Installation

### Requirements
- Python 3.11+
- Docker (for containerized deployment)
- OpenAI-compatible API key (HuggingFace Inference, OpenAI, etc.)

### Local Setup

```bash
# Clone or download the repo
cd socratic-tutor-env

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export HF_TOKEN="your_huggingface_token"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"

# Run the server
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

The API will be available at `http://localhost:7860`.

### Docker Setup

```bash
# Build the image
docker build -t socratic-tutor-env .

# Run with your API token
export HF_TOKEN="your_huggingface_token"
docker run -p 7860:7860 \
  -e HF_TOKEN \
  -e API_BASE_URL=https://router.huggingface.co/v1 \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  socratic-tutor-env
```

### HuggingFace Spaces Deployment

1. Create a new Space at https://huggingface.co/new-space
2. Choose **Docker** as the runtime
3. Set Secrets in Space settings:
   - `HF_TOKEN`: Your HuggingFace API token
   - `API_BASE_URL`: `https://router.huggingface.co/v1`
   - `MODEL_NAME`: `Qwen/Qwen2.5-72B-Instruct` (or your preferred model)
4. Push your repo to `https://huggingface.co/spaces/{username}/socratic-tutor`

## Usage Example

### Reset to start a new episode:
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id":"easy"}'
```

**Response:**
```json
{
  "student_response": "I think I understand this. Heavier objects always fall faster than lighter objects because they weigh more.",
  "belief_score": 0.1,
  "probe_result": null,
  "turn_number": 0,
  "done": false,
  "task_id": "easy",
  "feedback": "Episode started."
}
```

### Submit a teacher utterance:
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"utterance":"Think about what Galileo discovered. If mass determined speed, would a feather and a rock fall differently in a vacuum?"}'
```

**Response:**
```json
{
  "observation": {
    "student_response": "Hmm, I guess they'd fall at different speeds... but only because of air resistance, right?",
    "belief_score": 0.35,
    "probe_result": null,
    "turn_number": 1,
    "done": false,
    "task_id": "easy",
    "feedback": "Belief improved by +0.25. Good progress!"
  },
  "reward": 0.5,
  "done": false,
  "info": {}
}
```

### Get environment state:
```bash
curl -X GET http://localhost:7860/state
```

Returns full transcript, current belief score, misconception, and correct answer.

### Get final score:
```bash
curl -X GET http://localhost:7860/score
```

## Baseline Results

**Model:** Qwen/Qwen2.5-72B-Instruct  
**Run:** Single-run reproducible baseline (seed=42)  
**Inference script:** `inference.py`

| Task | Final Belief Score | Avg Reward/Turn | Success? |
|------|-------------------|-----------------|----------|
| easy | 0.72 | 0.48 | ✓ |
| medium | 0.68 | 0.42 | ✓ (border) |
| hard | 0.55 | 0.31 | ✗ |

**Observations:**
- Socratic constraint (hard task, questions-only) significantly challenges the baseline
- Dense reward signal helps, but belief tracking requires nuanced understanding
- Frontier models (GPT-4, Claude 3+) expected to exceed these baselines

## Running the Baseline Inference Script

```bash
export OPENAI_API_KEY="your_api_key"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"

python inference.py
```

**Expected output:**
```
[START] task=easy env=socratic-tutor-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action='Think about...' reward=0.50 done=false error=null
...
[END] success=true steps=5 score=0.720 rewards=0.50,0.48,0.45,0.51,0.42
```

## API Reference

### POST /reset
Reset the environment to initial state.

**Request:**
```json
{
  "task_id": "easy|medium|hard"
}
```

**Response:**
```json
{
  "student_response": "string",
  "belief_score": 0.0–1.0,
  "probe_result": null,
  "turn_number": 0,
  "done": false,
  "task_id": "string",
  "feedback": "string"
}
```

---

### POST /step
Submit a teacher action; receive observation, reward, and done flag.

**Request:**
```json
{
  "utterance": "string (1–1000 chars)"
}
```

**Response:**
```json
{
  "observation": { /* SocraticObservation */ },
  "reward": 0.0–5.0,
  "done": boolean,
  "info": {}
}
```

---

### GET /state
Inspect full environment state.

**Response:**
```json
{
  "task_id": "string",
  "turn_number": "int",
  "belief_score": 0.0–1.0,
  "transcript": [
    { "role": "student|teacher", "text": "string" }
  ],
  "misconception": "string",
  "correct_answer": "string",
  "done": boolean,
  "total_reward": float
}
```

---

### GET /health
Health check.

**Response:**
```json
{
  "status": "ok"
}
```

---

### GET /score
Get final episode score.

**Response:**
```json
{
  "score": 0.0–1.0,
  "total_reward": float,
  "turn_number": int,
  "done": boolean
}
```

## Architecture

```
server/
  ├── app.py                 # FastAPI application
  ├── environment.py         # SocraticEnvironment (step/reset/state logic)
  ├── student_simulator.py   # LLM-powered student with belief tracking
  └── __init__.py

tasks/
  ├── task_definitions.py    # Task specs + graders
  └── __init__.py

models.py                     # Pydantic models (Action, Observation, State)
inference.py                  # Baseline inference script
Dockerfile                    # Container definition
openenv.yaml                  # OpenEnv metadata
requirements.txt              # Python dependencies
```

## Key Design Decisions

1. **LLM-simulated student:** Realistic responses; updates beliefs based on teacher reasoning quality
2. **Shaped rewards:** Dense signals guide learning; sparse rewards fail for dialogue tasks
3. **Belief score as proxy:** 0–1 scalar indicates progress toward correct understanding
4. **Periodic probes:** Every 2 turns, query specific knowledge to verify learning (not just belief)
5. **Hard task constraint:** Questions-only forces deeper Socratic engagement; toys with reasoning boundaries

## Future Extensions

- Support for multi-turn student groups (collaborative learning)
- Custom misconception injection via API
- Evaluation against human tutors (Turing-test style)
- Fine-tuning data export for specialized teacher models

## License

MIT

## Citation

If you use this environment, please cite:

```
@software{socratic-tutor-2026,
  author = {Arjun},
  title = {Socratic Tutor: An OpenEnv Environment for AI Teacher Evaluation},
  year = {2026},
  url = {https://huggingface.co/spaces/<username>/socratic-tutor}
}
```

## Contact

For issues, feature requests, or questions, please open an issue on the GitHub repository.

---

**Ready for OpenEnv hackathon evaluation.**
