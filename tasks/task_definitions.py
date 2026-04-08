TASKS = {
    "easy": {
        "task_id": "easy",
        "difficulty": "Easy",
        "context": "You are teaching a student about gravity and falling objects.",
        "misconception": (
            "Heavier objects always fall faster than lighter objects "
            "because they weigh more."
        ),
        "correct_answer": (
            "In the absence of air resistance, all objects fall at the same rate "
            "regardless of their mass. Galileo demonstrated this."
        ),
        "probe_questions": [
            (
                "If I drop a 1kg ball and a 10kg ball from the same height in a vacuum, "
                "which one hits the ground first?",
                ["same time", "same rate", "simultaneously", "both", "equal", "together"],
            ),
            (
                "What did Galileo show about falling objects?",
                ["same", "equal", "regardless", "mass", "rate"],
            ),
        ],
        "max_turns": 10,
        "socratic_only": False,
    },
    "medium": {
        "task_id": "medium",
        "difficulty": "Medium",
        "context": (
            "You are teaching a student about electricity. "
            "The student believes something incorrect about how circuits work."
        ),
        "misconception": (
            "Electricity is 'used up' as it flows through a circuit — "
            "there is less electricity coming out of a bulb than going in."
        ),
        "correct_answer": (
            "Electric charge is conserved. The same amount of current flows "
            "in and out of any component. What the bulb converts is energy, "
            "not charge. Current itself is not consumed."
        ),
        "probe_questions": [
            (
                "If 2 amps flow into a lightbulb, how many amps flow out?",
                ["2", "two", "same", "equal", "conserved"],
            ),
            (
                "What does a lightbulb actually consume — current or energy?",
                ["energy", "power", "not current", "current is conserved"],
            ),
        ],
        "max_turns": 8,
        "socratic_only": False,
    },
    "hard": {
        "task_id": "hard",
        "difficulty": "Hard",
        "context": (
            "You are a Socratic tutor teaching about evolution. "
            "IMPORTANT: You may ONLY ask questions. Never make direct statements. "
            "Every utterance must end with '?'."
        ),
        "misconception": (
            "Animals deliberately develop new traits because they need them — "
            "for example, giraffes grew long necks because they wanted to reach "
            "higher leaves."
        ),
        "correct_answer": (
            "Evolution happens through natural selection acting on random variation. "
            "Organisms do not deliberately acquire traits. Giraffes with randomly "
            "longer necks survived better and reproduced more, so the trait spread."
        ),
        "probe_questions": [
            (
                "Does an individual giraffe grow a longer neck because it wants to, "
                "or because of something else?",
                ["random", "variation", "selection", "not want", "survive", "reproduce", "chance"],
            ),
            (
                "What is the role of random variation in how traits spread?",
                ["random", "variation", "survive", "reproduce", "selection", "spread"],
            ),
        ],
        "max_turns": 8,
        "socratic_only": True,
    },
}