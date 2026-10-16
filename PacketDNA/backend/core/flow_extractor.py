"""
PacketDNA - Flow Extractor Module
==================================
Extracts bidirectional network flows from raw packets.

A flow is defined by the 5-tuple:
  (src_ip, dst_ip, src_port, dst_port, protocol)

Bidirectional flows group packets traveling in both directions
(A→B and B→A) under the same flow identifier.
"""

import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from config.settings import get_config

config = get_config()


@dataclass
class Packet:
    """Represents a single network packet's metadata."""
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int  # 6=TCP, 17=UDP
    size: int  # total packet size in bytes
    payload_size: int  # payload size (excluding headers)
    flags: int = 0  # TCP flags
    direction: int = 0  # 0 = forward, 1 = backward


@dataclass
class Flow:
    """Represents a bidirectional network flow."""
    flow_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    protocol_name: str
    start_time: float = 0.0
    end_time: float = 0.0
    packets: List[Packet] = field(default_factory=list)
    forward_packets: List[Packet] = field(default_factory=list)
    backward_packets: List[Packet] = field(default_factory=list)
    label: Optional[str] = None  # ground truth label if available

    @property
    def duration(self) -> float:
        """Flow duration in seconds."""
        if not self.packets:
            return 0.0
        return self.end_time - self.start_time

    @property
    def total_packets(self) -> int:
        """Total number of packets in the flow."""
        return len(self.packets)

    @property
    def total_bytes(self) -> int:
        """Total bytes transferred in the flow."""
        return sum(p.size for p in self.packets)

    @property
    def forward_bytes(self) -> int:
        """Total bytes in the forward direction."""
        return sum(p.size for p in self.forward_packets)

    @property
    def backward_bytes(self) -> int:
        """Total bytes in the backward direction."""
        return sum(p.size for p in self.backward_packets)

    def to_dict(self) -> dict:
        """Convert flow to dictionary representation."""
        return {
            "flow_id": self.flow_id,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 4),
            "total_packets": self.total_packets,
            "forward_packets": len(self.forward_packets),
            "backward_packets": len(self.backward_packets),
            "total_bytes": self.total_bytes,
            "forward_bytes": self.forward_bytes,
            "backward_bytes": self.backward_bytes,
            "label": self.label,
        }


class FlowExtractor:
    """
    Extracts bidirectional flows from a sequence of parsed packets.

    Packets are grouped by their 5-tuple (src_ip, dst_ip, src_port, 
    dst_port, protocol) into bidirectional flows. A canonical flow key
    is computed so that packets in both directions map to the same flow.

    Flows are expired after an idle timeout (no new packets for 
    FLOW_TIMEOUT seconds).
    """

    PROTOCOL_MAP = {
        1: "ICMP",
        6: "TCP",
        17: "UDP",
        47: "GRE",
        50: "ESP",
        58: "ICMPv6",
    }

    def __init__(self, timeout: float = None, min_packets: int = None):
        self.timeout = timeout or config.FLOW_TIMEOUT
        self.min_packets = min_packets or config.MIN_PACKETS_PER_FLOW
        self.active_flows: Dict[str, Flow] = {}
        self.completed_flows: List[Flow] = []
        self._stats = {
            "total_packets_processed": 0,
            "total_flows_created": 0,
            "total_flows_expired": 0,
            "invalid_packets_skipped": 0,
        }

    @staticmethod
    def _compute_flow_key(src_ip: str, dst_ip: str,
                          src_port: int, dst_port: int,
                          protocol: int) -> Tuple[str, bool]:
        """
        Compute a canonical bidirectional flow key.

        Returns:
            Tuple of (flow_key_hash, is_forward).
            is_forward is True if the packet is in the original direction.
        """
        # Canonical ordering: sort by IP, then port
        forward = (src_ip, src_port) <= (dst_ip, dst_port)
        if forward:
            key_tuple = (src_ip, dst_ip, src_port, dst_port, protocol)
        else:
            key_tuple = (dst_ip, src_ip, dst_port, src_port, protocol)

        key_str = "|".join(str(k) for k in key_tuple)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:16]

        return key_hash, forward

    def _get_protocol_name(self, protocol_num: int) -> str:
        """Get human-readable protocol name."""
        return self.PROTOCOL_MAP.get(protocol_num, f"PROTO_{protocol_num}")

    def add_packet(self, packet: Packet) -> Optional[str]:
        """
        Add a packet to the appropriate flow.

        Args:
            packet: Parsed packet metadata.

        Returns:
            Flow ID the packet was added to, or None if skipped.
        """
        self._stats["total_packets_processed"] += 1

        # Validate packet
        if not packet.src_ip or not packet.dst_ip:
            self._stats["invalid_packets_skipped"] += 1
            return None

        # Compute flow key
        flow_key, is_forward = self._compute_flow_key(
            packet.src_ip, packet.dst_ip,
            packet.src_port, packet.dst_port,
            packet.protocol
        )

        # Set packet direction
        packet.direction = 0 if is_forward else 1

        # Create or update flow
        if flow_key not in self.active_flows:
            # Determine canonical src/dst
            if is_forward:
                src_ip, dst_ip = packet.src_ip, packet.dst_ip
                src_port, dst_port = packet.src_port, packet.dst_port
            else:
                src_ip, dst_ip = packet.dst_ip, packet.src_ip
                src_port, dst_port = packet.dst_port, packet.src_port

            flow = Flow(
                flow_id=flow_key,
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=packet.protocol,
                protocol_name=self._get_protocol_name(packet.protocol),
                start_time=packet.timestamp,
                end_time=packet.timestamp,
            )
            self.active_flows[flow_key] = flow
            self._stats["total_flows_created"] += 1
        else:
            flow = self.active_flows[flow_key]

        # Add packet to flow
        flow.packets.append(packet)
        flow.end_time = max(flow.end_time, packet.timestamp)

        if is_forward:
            flow.forward_packets.append(packet)
        else:
            flow.backward_packets.append(packet)

        return flow_key

    def expire_flows(self, current_time: float = None) -> List[Flow]:
        """
        Expire flows that have been idle beyond the timeout.

        Args:
            current_time: Current timestamp. Defaults to now.

        Returns:
            List of expired flows.
        """
        if current_time is None:
            current_time = time.time()

        expired = []
        to_remove = []

        for key, flow in self.active_flows.items():
            if (current_time - flow.end_time) > self.timeout:
                if flow.total_packets >= self.min_packets:
                    expired.append(flow)
                    self.completed_flows.append(flow)
                to_remove.append(key)
                self._stats["total_flows_expired"] += 1

        for key in to_remove:
            del self.active_flows[key]

        return expired

    def finalize(self) -> List[Flow]:
        """
        Finalize all remaining active flows.
        Call this after all packets have been processed.

        Returns:
            List of all valid flows.
        """
        valid_flows = []
        for flow in self.active_flows.values():
            if flow.total_packets >= self.min_packets:
                valid_flows.append(flow)
                self.completed_flows.append(flow)

        self.active_flows.clear()
        return valid_flows

    def get_all_flows(self) -> List[Flow]:
        """Get all completed flows."""
        return self.completed_flows

    def get_stats(self) -> dict:
        """Get extraction statistics."""
        return {
            **self._stats,
            "active_flows": len(self.active_flows),
            "completed_flows": len(self.completed_flows),
        }

    def reset(self):
        """Reset the extractor state."""
        self.active_flows.clear()
        self.completed_flows.clear()
        self._stats = {
            "total_packets_processed": 0,
            "total_flows_created": 0,
            "total_flows_expired": 0,
            "invalid_packets_skipped": 0,
        }
