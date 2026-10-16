"""
PacketDNA - Feature Engine Module
==================================
Computes 22 statistical features from network flows for ML classification.

Features are computed from both forward and backward packet streams,
capturing the statistical "fingerprint" of the traffic without
inspecting payload content.

Feature Categories:
    1. Packet Size Statistics (forward + backward)
    2. Inter-Arrival Time (IAT) Statistics
    3. Flow-Level Aggregate Features
    4. Ratio and Proportion Features
"""

import math
from typing import List, Dict, Optional
from dataclasses import dataclass

import numpy as np

from core.flow_extractor import Flow, Packet


@dataclass
class FlowFeatures:
    """Container for all statistical features extracted from a flow."""
    flow_id: str
    feature_vector: List[float]
    feature_names: List[str]
    label: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary with feature names as keys."""
        features = dict(zip(self.feature_names, self.feature_vector))
        features["flow_id"] = self.flow_id
        if self.label:
            features["label"] = self.label
        return features


class FeatureEngine:
    """
    Computes statistical features from network flows.

    Extracts 22 features organized into four categories:
    - Packet size statistics (mean, std, min, max for fwd/bwd)
    - Inter-arrival time statistics (mean, std, min, max)
    - Flow-level aggregates (duration, byte rate, packet rate, total bytes)
    - Ratio features (fwd/bwd packet ratio, fwd/bwd byte ratio, avg payload)

    These features form a "fingerprint" that enables ML classifiers to
    identify the application or service generating the traffic without
    inspecting encrypted payloads.
    """

    FEATURE_NAMES = [
        # Packet size statistics (forward)
        "fwd_pkt_size_mean",
        "fwd_pkt_size_std",
        "fwd_pkt_size_min",
        "fwd_pkt_size_max",
        # Packet size statistics (backward)
        "bwd_pkt_size_mean",
        "bwd_pkt_size_std",
        "bwd_pkt_size_min",
        "bwd_pkt_size_max",
        # Inter-arrival time statistics
        "fwd_iat_mean",
        "fwd_iat_std",
        "bwd_iat_mean",
        "bwd_iat_std",
        # Flow-level aggregates
        "flow_duration",
        "flow_byte_rate",
        "flow_packet_rate",
        "total_fwd_bytes",
        "total_bwd_bytes",
        "total_packets",
        # Ratio and proportion features
        "fwd_bwd_packet_ratio",
        "fwd_bwd_byte_ratio",
        "avg_payload_size",
        "pkt_size_variation",
    ]

    def __init__(self):
        self._computed_count = 0

    @staticmethod
    def _safe_stats(values: List[float]) -> Dict[str, float]:
        """
        Compute safe statistics for a list of values.
        Returns zeros if the list is empty.
        """
        if not values:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

        arr = np.array(values, dtype=np.float64)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
        }

    @staticmethod
    def _compute_iat(packets: List[Packet]) -> List[float]:
        """
        Compute inter-arrival times between consecutive packets.

        Args:
            packets: List of packets sorted by timestamp.

        Returns:
            List of inter-arrival times in seconds.
        """
        if len(packets) < 2:
            return []

        sorted_pkts = sorted(packets, key=lambda p: p.timestamp)
        iats = []
        for i in range(1, len(sorted_pkts)):
            iat = sorted_pkts[i].timestamp - sorted_pkts[i - 1].timestamp
            iats.append(max(0.0, iat))  # ensure non-negative

        return iats

    def extract_features(self, flow: Flow) -> FlowFeatures:
        """
        Extract all 22 statistical features from a single flow.

        Args:
            flow: A bidirectional network flow.

        Returns:
            FlowFeatures object containing the feature vector.
        """
        # --- 1. Packet Size Statistics (Forward) ---
        fwd_sizes = [p.size for p in flow.forward_packets]
        fwd_stats = self._safe_stats(fwd_sizes)

        # --- 2. Packet Size Statistics (Backward) ---
        bwd_sizes = [p.size for p in flow.backward_packets]
        bwd_stats = self._safe_stats(bwd_sizes)

        # --- 3. Inter-Arrival Time Statistics ---
        fwd_iats = self._compute_iat(flow.forward_packets)
        fwd_iat_stats = self._safe_stats(fwd_iats)

        bwd_iats = self._compute_iat(flow.backward_packets)
        bwd_iat_stats = self._safe_stats(bwd_iats)

        # --- 4. Flow-Level Aggregates ---
        duration = flow.duration
        total_bytes = flow.total_bytes
        total_packets = flow.total_packets

        byte_rate = total_bytes / duration if duration > 0 else 0.0
        packet_rate = total_packets / duration if duration > 0 else 0.0

        # --- 5. Ratio and Proportion Features ---
        bwd_pkts = len(flow.backward_packets)
        fwd_bwd_pkt_ratio = (
            len(flow.forward_packets) / bwd_pkts
            if bwd_pkts > 0
            else float(len(flow.forward_packets))
        )

        bwd_bytes = flow.backward_bytes
        fwd_bwd_byte_ratio = (
            flow.forward_bytes / bwd_bytes
            if bwd_bytes > 0
            else float(flow.forward_bytes)
        )

        # Average payload size
        all_payload_sizes = [p.payload_size for p in flow.packets]
        avg_payload = np.mean(all_payload_sizes) if all_payload_sizes else 0.0

        # Packet size variation (coefficient of variation)
        all_sizes = [p.size for p in flow.packets]
        if all_sizes and np.mean(all_sizes) > 0:
            pkt_size_variation = float(np.std(all_sizes) / np.mean(all_sizes))
        else:
            pkt_size_variation = 0.0

        # --- Assemble Feature Vector ---
        feature_vector = [
            fwd_stats["mean"],
            fwd_stats["std"],
            fwd_stats["min"],
            fwd_stats["max"],
            bwd_stats["mean"],
            bwd_stats["std"],
            bwd_stats["min"],
            bwd_stats["max"],
            fwd_iat_stats["mean"],
            fwd_iat_stats["std"],
            bwd_iat_stats["mean"],
            bwd_iat_stats["std"],
            duration,
            byte_rate,
            packet_rate,
            float(flow.forward_bytes),
            float(flow.backward_bytes),
            float(total_packets),
            fwd_bwd_pkt_ratio,
            fwd_bwd_byte_ratio,
            float(avg_payload),
            pkt_size_variation,
        ]

        # Replace NaN/Inf with 0
        feature_vector = [
            0.0 if (math.isnan(v) or math.isinf(v)) else round(v, 6)
            for v in feature_vector
        ]

        self._computed_count += 1

        return FlowFeatures(
            flow_id=flow.flow_id,
            feature_vector=feature_vector,
            feature_names=self.FEATURE_NAMES.copy(),
            label=flow.label,
        )

    def extract_batch(self, flows: List[Flow]) -> List[FlowFeatures]:
        """
        Extract features from multiple flows.

        Args:
            flows: List of network flows.

        Returns:
            List of FlowFeatures objects.
        """
        return [self.extract_features(flow) for flow in flows]

    def to_matrix(self, features_list: List[FlowFeatures]) -> np.ndarray:
        """
        Convert list of FlowFeatures to a numpy feature matrix.

        Args:
            features_list: List of FlowFeatures.

        Returns:
            2D numpy array of shape (n_flows, n_features).
        """
        if not features_list:
            return np.array([])

        return np.array([f.feature_vector for f in features_list])

    def get_feature_names(self) -> List[str]:
        """Get the list of feature names."""
        return self.FEATURE_NAMES.copy()

    @property
    def computed_count(self) -> int:
        """Number of flows processed."""
        return self._computed_count
