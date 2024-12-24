from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union
from abc import ABC, abstractmethod

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

@dataclass
class IPNetwork(NetworkInterface):
    name: str
    type: str
    ip: Optional[str] = None
    subnet_mask: Optional[str] = None
    mac: Optional[str] = None

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> str:
        return self.type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "ip": self.ip,
            "subnet_mask": self.subnet_mask,
            "mac": self.mac,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IPNetwork':
        return cls(
            name=data.get("name"),
            type=data.get("type"),
            ip=data.get("ip"),
            subnet_mask=data.get("subnet_mask"),
            mac=data.get("mac"),
        )

    def __repr__(self) -> str:
        return self.to_dict().__repr__()

@dataclass
class CIDRNetwork(NetworkInterface):
    name: str
    type: str
    cidrs: Optional[List[str]] = field(default_factory=list)

    def get_name(self) -> str:
        return self.name
    
    def get_type(self) -> str:
        return self.type

    def to_dict(self) -> Dict[str, Union[str, List[str], None]]:
        return {
            "name": self.name,
            "type": self.type,
            "cidrs": self.cidrs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, List[str], None]]) -> 'CIDRNetwork':
        return cls(
            name=data.get("name"),
            type=data.get("type"),
            cidrs=data.get("cidrs")
        )

    def __repr__(self) -> str:
        return self.to_dict().__repr__()

@dataclass
class HostSubnetNetwork(NetworkInterface):
    name: str
    type: str
    hostname: Optional[str] = ""
    egress_cidrs: Optional[List[str]] = field(default_factory=list)
    egress_ips: Optional[List[str]] = field(default_factory=list)

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> str:
        return self.type

    def to_dict(self) -> Dict[str, Union[str, List[str], None]]:
        return {
            "name": self.name,
            "type": self.type,
            "hostname": self.hostname,
            "egress_cidrs": self.egress_cidrs,
            "egress_ips": self.egress_ips
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HostSubnetNetwork':
        return cls(
            name=data.get("name"),
            type=data.get("type"),
            hostname=data.get("hostname"),
            egress_cidrs=data.get("egress_cidrs"),
            egress_ips=data.get("egress_ips")
        )

    def __repr__(self) -> str:
        return self.to_dict().__repr__()

# Map type strings to their corresponding classes
NETWORK_TYPE_MAP: Dict[str, Type[NetworkInterface]] = {
    "ip": IPNetwork,
    "cidr": CIDRNetwork,
    "hostsubnet": HostSubnetNetwork,
}

def create_network(data: Dict[str, Any]) -> NetworkInterface:
    network_type = data.get("type")
    if not network_type:
        raise ValueError("The 'type' field is required in the data.")

    network_class = NETWORK_TYPE_MAP.get(network_type.lower())
    if not network_class:
        raise ValueError(f"Unknown network type: {network_type}")

    return network_class.from_dict(data)