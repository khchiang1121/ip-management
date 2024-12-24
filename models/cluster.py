from datetime import datetime, timezone
from typing import Any, List, Dict, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from models.network import NetworkInterface, create_network


@dataclass
class Source:
    env_config: Optional[str]= None
    owners: Optional[List[str]] = None
    cilium_cluster_id: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
    networks: Optional[List[NetworkInterface]] = None
    last_updated: datetime = datetime.now(timezone.utc)

    def to_dict(self):
        result = {
            "env_config": self.env_config,
            "owners": self.owners,
            "cilium_cluster_id": self.cilium_cluster_id,
            "additional_info": self.additional_info if self.additional_info else {},
            "networks": ([network.to_dict() for network in self.networks] if self.networks else None),
            "last_updated": self.last_updated,
        }
        return {key: value for key, value in result.items() if value is not None}
        
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Source':
        networks = [create_network(network_data) for network_data in data["networks"]] if data.get("networks") else None
        
        last_updated = None
        if data.get("last_updated") and isinstance(data["last_updated"], str):
            try:
                last_updated = datetime.fromisoformat(data["last_updated"])
            except ValueError:
                last_updated = None

        return cls(
            env_config=data.get("env_config"),
            owners=data.get("owners"),
            cilium_cluster_id=data.get("cilium_cluster_id"),
            additional_info=data.get("additional_info"),
            networks=networks,
            last_updated=last_updated
        )
    
    def refresh_last_updated(self) -> None:
        self.last_updated = datetime.now(timezone.utc)
          
    def __repr__(self) -> str:
        return self.to_dict().__repr__()

    # def __repr__(self):
    #     return (
    #         f"<Source(networks={self.networks}, env_config={self.env_config}, owners={self.owners}, cilium_cluster_id={self.cilium_cluster_id}, additional_info={self.additional_info}, last_updated={self.last_updated})>"
    #     )

@dataclass
class Cluster:
    cluster_id: str
    cluster_name: Optional[str] = None
    env_config: Optional[str] = None
    owners: Optional[List[str]] = None
    cilium_cluster_id: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
    networks: Optional[List[NetworkInterface]] = None
    sources: Optional[Dict[str, Source]] = None
    last_updated: datetime = datetime.now(timezone.utc)

    def __post_init__(self):
        if self.cluster_id is None and self.env_config is None:
            raise ValueError("cluster_id or env_config cannot be None")
        if self.cluster_id is None:
            self.cluster_id = self.env_config
        if self.env_config is None:
            self.env_config = self.cluster_id

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cluster':
        networks = [create_network(network_data) for network_data in data["networks"]] if data.get("networks") else None
        sources = {key: Source.from_dict(source_data) for key, source_data in data["sources"].items()} if data.get("sources") else None
        if data.get("cluster_id") is None and data.get("env_config") is not None:
            data["cluster_id"] = data["env_config"]
        elif data.get("env_config") is None and data.get("cluster_id") is not None:
            data["env_config"] = data["cluster_id"]
            
        last_updated = None
        if data.get("last_updated") and isinstance(data["last_updated"], str):
            try:
                last_updated = datetime.fromisoformat(data["last_updated"])
            except ValueError:
                last_updated = None
            
        return cls(
            cluster_id=data.get("cluster_id"),
            cluster_name=data.get("cluster_name"),
            env_config=data.get("env_config"),
            owners=data.get("owners"),
            cilium_cluster_id=data.get("cilium_cluster_id"),
            additional_info=data.get("additional_info"),
            networks=networks,
            sources=sources,
            last_updated=last_updated
        )
    
    def to_dict(self):
        result = {
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "env_config": self.env_config,
            "owners": self.owners,
            "cilium_cluster_id": self.cilium_cluster_id,
            "additional_info": self.additional_info if self.additional_info else {},
            "networks": ([network.to_dict() for network in self.networks] if self.networks else None),
            "sources": ({key: source.to_dict() for key, source in self.sources.items()} if self.sources else None),
            "last_updated": self.last_updated.isoformat()
        }
        return {key: value for key, value in result.items() if value is not None} 

    @staticmethod
    def _create_source(source_data: Dict[str, Any]) -> Source:
        networks = [create_network(network_data) for network_data in source_data["networks"]] if source_data.get("networks") else None
        return Source(
            env_config=source_data.get("env_config", None),
            owners=source_data.get("owners", None),
            cilium_cluster_id=source_data.get("cilium_cluster_id", None),
            networks=networks, 
            last_updated=datetime.fromisoformat(source_data["last_updated"]),
            additional_info=source_data.get("additional_info", {})
        )
    
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
    
    def refresh_last_updated(self) -> None:
        self.last_updated = datetime.now(timezone.utc)
    
    def refresh_source_last_updated(self, source_name: str) -> None:
        if self.sources and source_name in self.sources.keys():
            self.sources[source_name].refresh_last_updated()

    def __repr__(self) -> str:
        return self.to_dict().__repr__()
