class StateMachine:
    def __init__(self, steps: list):
        self.steps = steps

    def run(self, context: dict):
        for step in self.steps:
            step.run(context)
