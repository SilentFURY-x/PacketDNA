"""
PacketDNA - PCAP Parser Module
================================
Parses PCAP/PCAPNG files and extracts packet metadata.

Supports parsing via dpkt library with fallback to scapy.
Handles TCP, UDP, ICMP and other IP protocols.
"""

import struct
import os
from typing import List, Generator, Optional

from core.flow_extractor import Packet


class PcapParser:
    """
    Parses PCAP files and yields Packet objects.

    Uses dpkt for high-performance PCAP parsing. Extracts IP-layer
    and transport-layer metadata without inspecting payload content
    (privacy-preserving by design).
    """

    def __init__(self):
        self._packet_count = 0
        self._error_count = 0
        self._file_info = {}

    def parse_file(self, filepath: str) -> List[Packet]:
        """
        Parse a PCAP file and return list of Packet objects.

        Args:
            filepath: Path to the PCAP/PCAPNG file.

        Returns:
            List of parsed Packet objects.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file format is unsupported.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PCAP file not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()
        if ext not in (".pcap", ".pcapng", ".cap"):
            raise ValueError(f"Unsupported file format: {ext}")

        self._packet_count = 0
        self._error_count = 0

        packets = []
        try:
            packets = self._parse_with_dpkt(filepath)
        except Exception:
            try:
                packets = self._parse_with_scapy(filepath)
            except Exception as e:
                raise ValueError(f"Failed to parse PCAP file: {e}")

        self._file_info = {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "file_size": os.path.getsize(filepath),
            "total_packets": self._packet_count,
            "parse_errors": self._error_count,
            "valid_packets": len(packets),
        }

        return packets

    def _parse_with_dpkt(self, filepath: str) -> List[Packet]:
        """Parse PCAP using dpkt library."""
        import dpkt

        packets = []

        with open(filepath, "rb") as f:
            try:
                pcap = dpkt.pcap.Reader(f)
            except ValueError:
                f.seek(0)
                pcap = dpkt.pcapng.Reader(f)

            for timestamp, buf in pcap:
                self._packet_count += 1
                try:
                    pkt = self._parse_ethernet_frame(timestamp, buf)
                    if pkt:
                        packets.append(pkt)
                except Exception:
                    self._error_count += 1

        return packets

    def _parse_ethernet_frame(self, timestamp: float, buf: bytes) -> Optional[Packet]:
        """Parse an Ethernet frame and extract IP/transport layer info."""
        import dpkt

        try:
            eth = dpkt.ethernet.Ethernet(buf)
        except (dpkt.NeedData, dpkt.UnpackError):
            return None

        # Only process IP packets
        if not isinstance(eth.data, dpkt.ip.IP):
            return None

        ip = eth.data
        src_ip = self._ip_to_str(ip.src)
        dst_ip = self._ip_to_str(ip.dst)
        protocol = ip.p
        total_size = len(buf)

        src_port = 0
        dst_port = 0
        flags = 0
        payload_size = len(ip.data.data) if hasattr(ip.data, "data") else 0

        # Extract transport layer info
        if isinstance(ip.data, dpkt.tcp.TCP):
            tcp = ip.data
            src_port = tcp.sport
            dst_port = tcp.dport
            flags = tcp.flags
            payload_size = len(tcp.data)
        elif isinstance(ip.data, dpkt.udp.UDP):
            udp = ip.data
            src_port = udp.sport
            dst_port = udp.dport
            payload_size = len(udp.data)

        return Packet(
            timestamp=timestamp,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            size=total_size,
            payload_size=payload_size,
            flags=flags,
        )

    def _parse_with_scapy(self, filepath: str) -> List[Packet]:
        """Fallback parser using scapy."""
        from scapy.all import rdpcap, IP, TCP, UDP

        packets = []
        scapy_packets = rdpcap(filepath)

        for pkt in scapy_packets:
            self._packet_count += 1
            try:
                if not pkt.haslayer(IP):
                    continue

                ip_layer = pkt[IP]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                protocol = ip_layer.proto
                total_size = len(pkt)

                src_port = 0
                dst_port = 0
                flags = 0
                payload_size = 0

                if pkt.haslayer(TCP):
                    tcp_layer = pkt[TCP]
                    src_port = tcp_layer.sport
                    dst_port = tcp_layer.dport
                    flags = int(tcp_layer.flags)
                    payload_size = len(tcp_layer.payload)
                elif pkt.haslayer(UDP):
                    udp_layer = pkt[UDP]
                    src_port = udp_layer.sport
                    dst_port = udp_layer.dport
                    payload_size = len(udp_layer.payload)

                packets.append(Packet(
                    timestamp=float(pkt.time),
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=src_port,
                    dst_port=dst_port,
                    protocol=protocol,
                    size=total_size,
                    payload_size=payload_size,
                    flags=flags,
                ))
            except Exception:
                self._error_count += 1

        return packets

    @staticmethod
    def _ip_to_str(ip_bytes: bytes) -> str:
        """Convert IP bytes to string representation."""
        try:
            return ".".join(str(b) for b in ip_bytes)
        except Exception:
            return "0.0.0.0"

    def get_file_info(self) -> dict:
        """Get information about the last parsed file."""
        return self._file_info

    @property
    def packet_count(self) -> int:
        """Total packets processed in last parse."""
        return self._packet_count

    @property
    def error_count(self) -> int:
        """Parse errors in last parse."""
        return self._error_count
