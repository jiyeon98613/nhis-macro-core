from abc import ABC, abstractmethod

class BaseStep(ABC):
    @abstractmethod
    def run(self, context: dict) -> None:
        pass
