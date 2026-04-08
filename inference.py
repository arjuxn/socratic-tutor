import os
import sys
import json
import textwrap
from typing import List, Dict, Any
import requests
from openai import OpenAI

# Configuration
ENV_URL      = os.getenv("ENV_URL", "http://localhost:7860")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK    = "socratic-tutor-env"
MAX_STEPS    = 8
TEMPERATURE  = 0.7
MAX_TOKENS   = 200
SUCCESS_SCORE_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert teacher helping a student correct a misconception.
    Guide them toward correct understanding through questions and examples.
    For tasks requiring Socratic method, you MUST only ask questions ending with '?'.
    Keep responses under 3 sentences. Be patient and conversational.
""").strip()


def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str = None):
    error_val = error if error else "null"
    action_safe = action.replace("\n", " ")[:80]
    print(f"[STEP] step={step} action={action_safe!r} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def get_teacher_message(client: OpenAI, step: int, student_response: str, belief_score: float, 
                       feedback: str, history: List[str], task_context: str) -> str:
    """Get next teacher utterance from LLM."""
    history_block = "\n".join(history[-4:]) if history else "None"
    prompt = textwrap.dedent(f"""
        Task: {task_context}
        Student said: "{student_response}"
        Belief score: {belief_score:.2f} (0=wrong, 1=correct)
        Feedback from last turn: {feedback}
        Turn {step} of {MAX_STEPS}
        Recent history:
        {history_block}
        
        Your next message as teacher:
    """).strip()
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text if text else "Can you tell me more about what you think?"
    except Exception as exc:
        print(f"[ERROR] LLM error: {str(exc)[:100]}", flush=True)
        return "Can you explain your reasoning?"


def reset_env(task_id: str = "easy") -> Dict[str, Any]:
    """Reset environment for a new episode."""
    try:
        response = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Reset failed: {e}", flush=True)
        sys.exit(1)


def step_env(utterance: str) -> Dict[str, Any]:
    """Submit teacher utterance to environment."""
    try:
        response = requests.post(f"{ENV_URL}/step", json={"utterance": utterance}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Step failed: {e}", flush=True)
        return {"observation": {}, "reward": 0.0, "done": True, "info": {}}


def get_score() -> Dict[str, Any]:
    """Get final episode score."""
    try:
        response = requests.get(f"{ENV_URL}/score", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Score fetch failed: {e}", flush=True)
        return {"score": 0.0}


def run_task(client: OpenAI, task_id: str) -> float:
    """Run a single task with the teacher LLM."""
    from tasks.task_definitions import TASKS
    
    if task_id not in TASKS:
        print(f"[ERROR] Unknown task: {task_id}", flush=True)
        return 0.0
    
    task_context = TASKS[task_id]["context"]
    rewards: List[float] = []
    history: List[str] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset episode
        result = reset_env(task_id=task_id)
        student_response = result.get("student_response", "")
        belief_score = result.get("belief_score", 0.1)
        feedback = result.get("feedback", "")
        done = result.get("done", False)

        # Run steps
        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            # Get teacher message from LLM
            message = get_teacher_message(
                client, step, student_response, belief_score, feedback, history, task_context
            )

            # Step environment
            step_result = step_env(message)
            obs = step_result.get("observation", {})
            reward = step_result.get("reward", 0.0)
            done = step_result.get("done", False)

            rewards.append(reward)
            steps_taken = step
            student_response = obs.get("student_response", "")
            belief_score = obs.get("belief_score", 0.0)
            feedback = obs.get("feedback", "")

            log_step(step=step, action=message, reward=reward, done=done, error=None)
            history.append(f"T{step}: {message[:50]}...")

            if done:
                break

        # Get final score
        score_data = get_score()
        score = score_data.get("score", 0.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[ERROR] Task execution failed: {e}", flush=True)
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


def main():
    """Main inference loop."""
    print(f"[CONFIG] ENV_URL={ENV_URL} MODEL={MODEL_NAME} API_BASE_URL={API_BASE_URL}", flush=True)
    
    # Initialize LLM client
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    # Run all tasks
    scores = {}
    for task_id in ["easy", "medium", "hard"]:
        scores[task_id] = run_task(client, task_id)
    
    # Print summary
    avg_score = sum(scores.values()) / len(scores) if scores else 0.0
    print(f"\n[SUMMARY]", flush=True)
    print(f"  easy={scores.get('easy', 0.0):.3f}", flush=True)
    print(f"  medium={scores.get('medium', 0.0):.3f}", flush=True)
    print(f"  hard={scores.get('hard', 0.0):.3f}", flush=True)
    print(f"  average={avg_score:.3f}", flush=True)


if __name__ == "__main__":
    main()