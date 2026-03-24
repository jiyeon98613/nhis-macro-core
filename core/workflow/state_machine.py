# core/workflow/state_machine.py
"""
core/workflow/state_machine.py — 스텝 순차 실행 엔진
=====================================================
Step 리스트를 순서대로 실행하며, 실패 시 재시도(r)/건너뛰기(s)/종료(q)를
사용자에게 선택하게 함.
"""

import logging

class StateMachine:
    def __init__(self, steps: list):
        self.steps = steps

    def run(self, context: dict) -> None:
        """등록된 Step을 순차 실행합니다. 실패 시 사용자에게 r/s/q를 선택받습니다."""
        i = 0
        while i < len(self.steps):
            step = self.steps[i]
            try:
                step.run(context)
                i += 1              # 성공 시 다음 단계로
            except Exception as e:
                choice = step.handle_failure(e)
                if choice == 'r':    # Retry: 현재 인덱스 유지 (루프 재시작)
                    
                    continue
                elif choice == 's':  # Skip: 다음 인덱스로 이동
                    
                    i += 1
                elif choice == 'q':  # Quit: 루프 즉시 종료
                    # 프로그램 종료 전 DB 핸들러 flush
                    logging.getLogger("nhis").handlers[-1].flush()
                    raise SystemExit
                    
        # 모든 스텝 완료 후 남은 버퍼 flush
        for handler in logging.getLogger("nhis").handlers:
            handler.flush()