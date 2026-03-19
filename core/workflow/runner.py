# core/workflow/runner.py

#외부 엔진에서 호출하는 진입점
from .state_machine import StateMachine

class WorkflowRunner:
    def __init__(self, steps: list):
        self.machine = StateMachine(steps)

    def run(self, context: dict):
        self.machine.run(context)
