# core/workflow/runner.py
"""
core/workflow/runner.py — 워크플로우 실행 진입점
=================================================
engine(main.py)에서 호출하는 최상위 인터페이스.
StateMachine을 감싸서 Step 리스트를 실행.
"""

#외부 엔진에서 호출하는 진입점
from .state_machine import StateMachine

class WorkflowRunner:

    def __init__(self, steps: list):
        """Step 리스트를 받아 StateMachine을 초기화합니다."""

        self.machine = StateMachine(steps)

    def run(self, context: dict):
        """워크플로우를 실행합니다."""
        
        self.machine.run(context)
