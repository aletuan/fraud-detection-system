from dataclasses import dataclass
from typing import List, Optional

@dataclass
class KafkaConfig:
    bootstrap_servers: str
    group_id: str
    auto_offset_reset: str = 'earliest'
    enable_auto_commit: bool = False
    max_poll_interval_ms: int = 300000  # 5 minutes
    session_timeout_ms: int = 45000     # 45 seconds
    heartbeat_interval_ms: int = 15000  # 15 seconds
    max_partition_fetch_bytes: int = 1048576  # 1MB
    fetch_max_bytes: int = 52428800  # 50MB
    topics: List[str] = None
    
    # Security configs
    security_protocol: Optional[str] = None
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert config to dict format for confluent_kafka.Consumer"""
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': self.auto_offset_reset,
            'enable.auto.commit': self.enable_auto_commit,
            'max.poll.interval.ms': self.max_poll_interval_ms,
            'session.timeout.ms': self.session_timeout_ms,
            'heartbeat.interval.ms': self.heartbeat_interval_ms,
            'max.partition.fetch.bytes': self.max_partition_fetch_bytes,
            'fetch.max.bytes': self.fetch_max_bytes,
        }

        # Add security configs if provided
        if self.security_protocol:
            config['security.protocol'] = self.security_protocol
        if self.sasl_mechanism:
            config['sasl.mechanism'] = self.sasl_mechanism
        if self.sasl_username:
            config['sasl.username'] = self.sasl_username
        if self.sasl_password:
            config['sasl.password'] = self.sasl_password

        return config 