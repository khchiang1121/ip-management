from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass

from models.network import NetworkInterface, create_network


@dataclass
class Source:
    hostname: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    datacenter: Optional[str] = None
    room: Optional[str] = None
    rack: Optional[str] = None
    unit: Optional[str] = None
    os: Optional[str] = None
    as_number: Optional[int] = None
    owner: Optional[str] = None
    cluster_id: Optional[str] = None
    env_config: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
    networks: Optional[List[NetworkInterface]] = None
    last_updated: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "hostname": self.hostname,
            "serial_number": self.serial_number,
            "location": self.location,
            "datacenter": self.datacenter,
            "room": self.room,
            "rack": self.rack,
            "unit": self.unit,
            "os": self.os,
            "as_number": self.as_number,
            "owner": self.owner,
            "cluster_id": self.cluster_id,
            "env_config": self.env_config,
            "additional_info": self.additional_info if self.additional_info else None,
            "networks": ([network.to_dict() for network in self.networks] if self.networks else None),
            "last_updated": self.last_updated,
        }
        # Remove keys with None values
        return {key: value for key, value in result.items() if value is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Source":
        networks = [create_network(network_data) for network_data in data["networks"]] if data.get("networks") else None
        
        last_updated = None
        if data.get("last_updated") and isinstance(data["last_updated"], str):
            try:
                last_updated = datetime.fromisoformat(data["last_updated"])
            except ValueError:
                last_updated = None

        return Source(
            hostname=data.get("hostname"),
            serial_number=data.get("serial_number"),
            location=data.get("location"),
            datacenter=data.get("datacenter"),
            room=data.get("room"),
            rack=data.get("rack"),
            unit=data.get("unit"),
            os=data.get("os"),
            as_number=data.get("as_number"),
            owner=data.get("owner"),
            cluster_id=data.get("cluster_id"),
            env_config=data.get("env_config"),
            additional_info=data.get("additional_info"),
            networks=(networks if networks else None),
            last_updated=last_updated
        )
    
    def refresh_last_updated(self) -> None:
        self.last_updated = datetime.now(timezone.utc)
        
    def __repr__(self) -> str:
        return self.to_dict().__repr__()

@dataclass
class Server:
    server_id: str
    hostname: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    datacenter: Optional[str] = None
    room: Optional[str] = None
    rack: Optional[str] = None
    unit: Optional[str] = None
    os: Optional[str] = None
    as_number: Optional[int] = None
    owner: Optional[str] = None
    cluster_id: Optional[str] = None
    env_config: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
    networks:  Optional[List[NetworkInterface]] = None
    sources:  Optional[Dict[str, Source]] = None
    last_updated: datetime = datetime.now(timezone.utc)

    def __post_init__(self):
        if self.server_id is None:
            raise ValueError("server_id cannot be None")
        if self.cluster_id is None and self.env_config is not None:
            self.cluster_id = self.env_config
        if self.env_config is None and self.cluster_id is not None:
            self.env_config = self.cluster_id

    def add_network(self, network: NetworkInterface) -> None:
        if self.networks:
            self.networks.append(network)
        else:
            self.networks = [ network ]
            
    def add_source(self, source_name: str, source_data: Dict[str, Any]):
        if self.sources and source_name in self.sources:
            self.sources[source_name] = Source.from_dict(source_data)
        else:
            self.sources = { source_name: Source.from_dict(source_data)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Server':
        # Create networks and sources based on data
        networks = [create_network(network_data) for network_data in data["networks"]] if data.get("networks") else None
        sources = {key: Source.from_dict(source_data) for key, source_data in data["sources"].items()} if data.get("sources") else None
        last_updated = None
        if data.get("last_updated") and isinstance(data["last_updated"], str):
            try:
                last_updated = datetime.fromisoformat(data["last_updated"])
            except ValueError:
                last_updated = None
        return cls(
            server_id=data.get("server_id"),
            hostname=data.get("hostname"),
            serial_number=data.get("serial_number"),
            location=data.get("location"),
            datacenter=data.get("datacenter"),
            room=data.get("room"),
            rack=data.get("rack"),
            unit=data.get("unit"),
            os=data.get("os"),
            as_number=data.get("as_number"),
            owner=data.get("owner"),
            cluster_id=data.get("cluster_id"),
            env_config=data.get("env_config"),
            additional_info=data.get("additional_info"),
            networks=(networks if networks else None),
            sources=(sources if sources else None),
            last_updated=last_updated
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "server_id": self.server_id,
            "hostname": self.hostname,
            "serial_number": self.serial_number,
            "location": self.location,
            "datacenter": self.datacenter,
            "room": self.room,
            "rack": self.rack,
            "unit": self.unit,
            "os": self.os,
            "as_number": self.as_number,
            "owner": self.owner,
            "cluster_id": self.cluster_id,
            "env_config": self.env_config,
            "additional_info": self.additional_info if self.additional_info else None,
            "networks": ([network.to_dict() for network in self.networks] if self.networks else None),
            "sources": ({key: source.to_dict() for key, source in self.sources.items()} if self.sources else None),
            "last_updated": self.last_updated,
        }
        return {key: value for key, value in result.items() if value is not None}
    
    # not in-used
    def sort_dict_by_order(self, input_dict, predefined_order):
        """
        Sort a dictionary by a predefined order of keys, appending other keys at the end.

        Args:
            input_dict (dict): The dictionary to be sorted.
            predefined_order (list): A list specifying the order of keys.

        Returns:
            dict: A new dictionary sorted by the predefined order, with other keys appended at the end.
        """
        # Create a set for faster lookup of predefined keys
        predefined_set = set(predefined_order)

        # Separate keys into predefined and others
        predefined_keys = [key for key in predefined_order if key in input_dict]
        other_keys = [key for key in input_dict if key not in predefined_set]

        # Combine sorted keys
        sorted_keys = predefined_keys + other_keys

        # Create the sorted dictionary
        return {key: input_dict[key] for key in sorted_keys}
    
    def refresh_last_updated(self) -> None:
        self.last_updated = datetime.now(timezone.utc)
    
    def refresh_source_last_updated(self, source_name: str) -> None:
        if source_name in self.sources:
            self.sources[source_name].refresh_last_updated()

    def __repr__(self) -> str:
        return self.to_dict().__repr__()
