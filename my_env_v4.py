import asyncio
import os
import subprocess
import time
from typing import Optional
import httpx
from pydantic import BaseModel


class MyEnvV4Action(BaseModel):
    message: str


class MyEnvV4Observation(BaseModel):
    student_response: str = ""
    belief_score: float = 0.0
    probe_result: Optional[float] = None
    turn_number: int = 0
    done: bool = False
    task_id: str = "easy"
    feedback: str = ""

    @property
    def echoed_message(self):
        return self.student_response


class StepResult(BaseModel):
    observation: MyEnvV4Observation
    reward: float = 0.0
    done: bool = False
    info: dict = {}


class MyEnvV4Env:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._container_proc = None

    @classmethod
    async def from_docker_image(cls, image_name: str, port: int = 7860):
        container_name = "socratic-tutor-env"
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        proc = subprocess.Popen([
            "docker", "run", "--rm",
            "--name", container_name,
            "-p", f"{port}:7860",
            "-e", f"HF_TOKEN={os.getenv('HF_TOKEN', '')}",
            "-e", f"API_BASE_URL={os.getenv('API_BASE_URL', 'https://router.huggingface.co/v1')}",
            "-e", f"MODEL_NAME={os.getenv('MODEL_NAME', 'Qwen/Qwen2.5-72B-Instruct')}",
            image_name,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        base_url = f"http://localhost:{port}"
        env = cls(base_url=base_url)
        env._container_proc = proc

        for _ in range(30):
            try:
                async with httpx.AsyncClient() as c:
                    r = await c.get(f"{base_url}/health", timeout=2.0)
                    if r.status_code == 200:
                        break
            except Exception:
                pass
            await asyncio.sleep(1.0)

        return env

    async def reset(self, task_id="easy"):
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as c:
            r = await c.post("/reset", json={"task_id": task_id})
            r.raise_for_status()
            data = r.json()
        obs = MyEnvV4Observation(**data)
        return StepResult(observation=obs, reward=0.0, done=False)

    async def step(self, action: MyEnvV4Action):
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as c:
            r = await c.post("/step", json={"utterance": action.message})
            r.raise_for_status()
            data = r.json()
        obs = MyEnvV4Observation(**data["observation"])
        return StepResult(
            observation=obs,
            reward=data.get("reward", 0.0),
            done=data.get("done", False),
            info=data.get("info", {}),
        )

    async def close(self):
        if self._container_proc:
            self._container_proc.terminate()