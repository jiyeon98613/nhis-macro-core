from .state_machine import StateMachine

class WorkflowRunner:
    def __init__(self, steps: list):
        self.machine = StateMachine(steps)

    def run(self, context: dict):
        self.machine.run(context)
