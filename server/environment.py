import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional, Tuple
from models import SocraticAction, SocraticObservation, SocraticState
from tasks.task_definitions import TASKS
from server.student_simulator import get_student_response, estimate_belief_score, run_probe


class SocraticEnvironment:
    MAX_TOTAL_REWARD = 5.0

    def __init__(self):
        self._reset_state()

    def _reset_state(self):
        self.task_id = "easy"
        self.task = TASKS["easy"]
        self.transcript = []
        self.turn_number = 0
        self.belief_score = 0.1
        self.done = False
        self.total_reward = 0.0
        self.cumulative_rewards = []

    def reset(self, task_id="easy"):
        if task_id not in TASKS:
            task_id = "easy"
        self._reset_state()
        self.task_id = task_id
        self.task = TASKS[task_id]
        self.belief_score = 0.1

        opening = f"I think I understand this. {self.task['misconception']}"
        self.transcript.append({"role": "student", "text": opening})

        return SocraticObservation(
            student_response=opening,
            belief_score=self.belief_score,
            probe_result=None,
            turn_number=0,
            done=False,
            task_id=self.task_id,
            feedback="Episode started.",
        )

    def step(self, action: SocraticAction):
        if self.done:
            obs = SocraticObservation(
                student_response="[Episode finished]",
                belief_score=self.belief_score,
                probe_result=None,
                turn_number=self.turn_number,
                done=True,
                task_id=self.task_id,
                feedback="Call reset() to start a new episode.",
            )
            return obs, 0.0, True, {}

        self.turn_number += 1
        teacher_utterance = action.utterance.strip()
        self.transcript.append({"role": "teacher", "text": teacher_utterance})

        student_response = get_student_response(
            teacher_utterance=teacher_utterance,
            misconception=self.task["misconception"],
            correct_answer=self.task["correct_answer"],
            history=self.transcript[:-1],
        )
        self.transcript.append({"role": "student", "text": student_response})

        previous_belief = self.belief_score
        self.belief_score = estimate_belief_score(
            student_response=student_response,
            misconception=self.task["misconception"],
            correct_answer=self.task["correct_answer"],
            previous_belief=previous_belief,
        )
        belief_delta = self.belief_score - previous_belief

        probe_result = None
        if self.turn_number % 2 == 0:
            rng = random.Random(42 + self.turn_number)
            probe_q, probe_kw = rng.choice(self.task["probe_questions"])
            probe_result = run_probe(
                probe_question=probe_q,
                expected_keywords=probe_kw,
                student_history=self.transcript,
                misconception=self.task["misconception"],
                correct_answer=self.task["correct_answer"],
                seed=42 + self.turn_number,
            )

        reward, feedback = self._compute_reward(belief_delta, probe_result, teacher_utterance)
        self.total_reward += reward
        self.cumulative_rewards.append(reward)

        max_turns_reached = self.turn_number >= self.task["max_turns"]
        understanding_achieved = self.belief_score >= 0.85 and probe_result == 1.0
        self.done = max_turns_reached or understanding_achieved

        obs = SocraticObservation(
            student_response=student_response,
            belief_score=self.belief_score,
            probe_result=probe_result,
            turn_number=self.turn_number,
            done=self.done,
            task_id=self.task_id,
            feedback=feedback,
        )
        return obs, reward, self.done, {}

    def _compute_reward(self, belief_delta, probe_result, teacher_utterance):
        reward = 0.0
        parts = []

        if probe_result is not None:
            if probe_result == 1.0:
                reward += 0.4
                parts.append("Probe passed (+0.4)")
            elif probe_result == 0.5:
                reward += 0.2
                parts.append("Probe partial (+0.2)")
            else:
                parts.append("Probe failed (0.0)")

        if belief_delta > 0.05:
            reward += 0.2
            parts.append(f"Belief up {belief_delta:+.2f} (+0.2)")
        elif belief_delta < -0.05:
            reward -= 0.2
            parts.append(f"Belief down {belief_delta:+.2f} (-0.2)")

        if self.transcript and "?" in self.transcript[-1]["text"]:
            reward += 0.1
            parts.append("Student engaged (+0.1)")

        if self.task.get("socratic_only") and not teacher_utterance.strip().endswith("?"):
            reward -= 0.1
            parts.append("Socratic violation (-0.1)")

        if self.turn_number > 4:
            reward -= 0.05
            parts.append("Efficiency penalty (-0.05)")

        reward = round(max(-0.5, min(0.7, reward)), 3)
        return reward, " | ".join(parts) if parts else "No signal this turn"

    def state(self):
        return SocraticState(
            task_id=self.task_id,
            turn_number=self.turn_number,
            belief_score=self.belief_score,
            transcript=self.transcript,
            misconception=self.task["misconception"],
            correct_answer=self.task["correct_answer"],
            done=self.done,
            total_reward=self.total_reward,
        )

    def final_score(self):
        score = self.total_reward / self.MAX_TOTAL_REWARD
        # Clamp to (0.001, 0.999) to ensure strictly between 0 and 1
        clamped = max(0.001, min(0.999, score))
        return round(clamped, 3)