# core/workflow/base_step.py

from abc import ABC, abstractmethod

class BaseStep(ABC):

    def __init__(self):
        self._log_buffer = []  # 로그 임시 저장소

    @property
    def name(self):
        """스텝의 이름을 클래스명으로 자동 설정"""
        return self.__class__.__name__

    @abstractmethod
    def run(self, context: dict) -> None:
        """모든 스텝이 공통으로 구현해야 하는 실행 로직"""
        pass

    def log(self, message: str, level: str = "INFO"):
        """콘솔 출력 + 버퍼에 적재 (DB는 아직 안 건드림)"""
        print(f"🔹 [{self.name}] {message}")
        self._log_buffer.append({
            "level": level,
            "step_name": self.name,
            "message": message
        })

    def flush_logs(self):
        """버퍼에 쌓인 로그를 한 번의 세션으로 DB에 일괄 저장"""
        if not self._log_buffer:
            return
            
        from core.db_manager import db
        from core.models import SystemLog
        
        session = db.get_runtime_session()
        try:
            for entry in self._log_buffer:
                session.add(SystemLog(
                    level=entry["level"],
                    step_name=entry["step_name"],
                    message=entry["message"]
                ))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"⚠️ 시스템 로그 저장 실패: {e}")
        finally:
            session.close()
            self._log_buffer.clear()  # 저장 후 비우기

    def handle_failure(self, error):
        """에러도 버퍼에 남긴 뒤 사용자 입력 받음"""
        self.log(f"오류 발생: {error}", level="ERROR")
        print(f"\n❌ [{self.name}] 실행 중 오류가 발생했습니다.")
        print(f"📝 상세 에러: {error}")
        
        while True:
            choice = input("👉 작업 선택 (r: 재시도, s: 건너뛰기, q: 전체 종료): ").lower().strip()
            if choice in ['r', 's', 'q']:
                return choice
            print("❗ 잘못된 입력입니다. r, s, q 중 하나를 입력하세요.")