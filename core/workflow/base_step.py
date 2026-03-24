# core/workflow/base_step.py
"""
core/workflow/base_step.py — 워크플로우 스텝 추상 클래스
========================================================
모든 Step(AuthStep, FileScanStep 등)의 부모 클래스.
run()을 반드시 구현해야 하며, log()와 handle_failure()를 공통 제공.
"""

from abc import ABC, abstractmethod
from core.logger import get_step_logger

class BaseStep(ABC):

    def __init__(self) -> str:
        self.logger = get_step_logger(self.name)

    @property
    def name(self):
        """스텝의 이름을 클래스명으로 자동 설정"""
        return self.__class__.__name__

    @abstractmethod
    def run(self, context: dict) -> None:
        pass

    def log(self, message: str, level: str = "INFO") -> None:
        """기존 self.log() 호출과 호환 유지"""
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
    
    # flush_logs() 삭제 — 핸들러가 알아서 처리함

    def handle_failure(self, error: Exception) -> str:
        self.logger.error(f"오류 발생: {error}", exc_info=True)  # ← 스택트레이스 자동 기록
        print(f"\n❌ [{self.name}] 실행 중 오류가 발생했습니다.")
        print(f"📝 상세 에러: {error}")
        while True:
            choice = input("👉 작업 선택 (r: 재시도, s: 건너뛰기, q: 전체 종료): ").lower().strip()
            if choice in ('r', 's', 'q'):
                return choice