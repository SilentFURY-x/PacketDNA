"""
PacketDNA - Flow Data Model
=============================
Data model for flow analysis results.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class FlowRecord:
    """Persistent flow record for storage."""
    flow_id: str
    session_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    duration: float
    total_packets: int
    forward_packets: int
    backward_packets: int
    total_bytes: int
    forward_bytes: int
    backward_bytes: int
    predicted_class: Optional[str] = None
    confidence: Optional[float] = None
    features: Optional[Dict] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "flow_id": self.flow_id,
            "session_id": self.session_id,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol,
            "duration": self.duration,
            "total_packets": self.total_packets,
            "forward_packets": self.forward_packets,
            "backward_packets": self.backward_packets,
            "total_bytes": self.total_bytes,
            "forward_bytes": self.forward_bytes,
            "backward_bytes": self.backward_bytes,
            "predicted_class": self.predicted_class,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }
