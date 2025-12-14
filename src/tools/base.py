# tools/base.py
from typing import Dict, Any
from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        pass
