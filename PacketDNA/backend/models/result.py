"""
PacketDNA - Result Data Model
===============================
Data model for classification and analysis results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class AnalysisResult:
    """Complete analysis result for a PCAP file."""
    session_id: str
    filename: str
    file_size: int
    total_packets: int
    valid_packets: int
    total_flows: int
    classified_flows: int
    protocol_distribution: Dict[str, int] = field(default_factory=dict)
    class_distribution: Dict[str, int] = field(default_factory=dict)
    model_type: str = "random_forest"
    accuracy: Optional[float] = None
    processing_time: float = 0.0
    flow_records: List[Dict] = field(default_factory=list)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "total_packets": self.total_packets,
            "valid_packets": self.valid_packets,
            "total_flows": self.total_flows,
            "classified_flows": self.classified_flows,
            "protocol_distribution": self.protocol_distribution,
            "class_distribution": self.class_distribution,
            "model_type": self.model_type,
            "accuracy": self.accuracy,
            "processing_time": round(self.processing_time, 4),
            "flow_records": self.flow_records,
            "feature_importance": self.feature_importance,
            "created_at": self.created_at,
        }

    @property
    def summary(self) -> dict:
        """Get a brief summary of the analysis."""
        return {
            "session_id": self.session_id,
            "filename": self.filename,
            "total_packets": self.total_packets,
            "total_flows": self.total_flows,
            "classified_flows": self.classified_flows,
            "top_class": max(self.class_distribution, key=self.class_distribution.get)
            if self.class_distribution
            else "unknown",
            "processing_time": round(self.processing_time, 4),
            "created_at": self.created_at,
        }
