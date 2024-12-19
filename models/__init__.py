from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union


class NetworkInterface(ABC):
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_type(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkInterface':
        pass
    
    @abstractmethod
    def __repr__(self) -> str:
        pass

    def __post_init__(self):
        if self.name is None:
            raise ValueError("name cannot be None")
        if self.type is None:
            raise ValueError("type cannot be None")
