# 단계 순서만 책임짐
# 실패 처리 로직은 나중에 추가
from .state_machine import StateMachine

class WorkflowRunner:
    def __init__(self, steps: list):
        self.machine = StateMachine(steps)

    def run(self, context: dict):
        self.machine.run(context)
