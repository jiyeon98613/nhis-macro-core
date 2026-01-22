..외부 엔진에서 호출하는 진입점
from abc import ABC, abstractmethod

class BaseStep(ABC):
    @abstractmethod
    def run(self, context: dict) -> None:
        pass
