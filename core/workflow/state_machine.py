# core/workflow/state_machine.py


class StateMachine:
    def __init__(self, steps: list):
        self.steps = steps

    def run(self, context: dict):
        i = 0
        while i < len(self.steps):
            step = self.steps[i]
            try:
                step.run(context)
                i += 1  # 성공 시 다음 단계로
            except Exception as e:
                choice = step.handle_failure(e)
                
                if choice == 'r':    # Retry: 현재 인덱스 유지 (루프 재시작)
                    print(f"🔄 [{step.name}] 재시도 중...")
                    continue
                elif choice == 's':  # Skip: 다음 인덱스로 이동
                    print(f"⏭️ [{step.name}] 단계를 건너뜁니다.")
                    i += 1
                elif choice == 'q':  # Quit: 루프 즉시 종료
                    print("🛑 사용자에 의해 시스템이 종료됩니다.")
                    raise SystemExit  # 아예 프로그램 종료