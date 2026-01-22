# 단계 순서만 책임짐
# 실패 처리 로직은 나중에 추가
class StateMachine:
    def __init__(self, steps: list):
        self.steps = steps

    def run(self, context: dict):
        for step in self.steps:
            step.run(context)
