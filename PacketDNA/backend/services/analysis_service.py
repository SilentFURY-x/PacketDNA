"""
PacketDNA - Analysis Service
==============================
Orchestrates the complete traffic analysis pipeline.

Pipeline:
    1. Parse PCAP file → raw packets
    2. Extract flows → bidirectional flows
    3. Compute features → statistical feature vectors
    4. Classify → predicted application categories
    5. Aggregate → analysis results
"""

import os
import time
import uuid
import random
from typing import List, Dict, Optional
from collections import Counter

import numpy as np

from config.settings import get_config
from core.pcap_parser import PcapParser
from core.flow_extractor import FlowExtractor, Flow, Packet
from core.feature_engine import FeatureEngine, FlowFeatures
from core.classifier import TrafficClassifier
from models.result import AnalysisResult

config = get_config()


class AnalysisService:
    """
    Orchestrates the end-to-end traffic analysis pipeline.

    Manages the flow from PCAP parsing through feature extraction
    to ML classification, producing comprehensive analysis results.
    """

    def __init__(self):
        self.parser = PcapParser()
        self.flow_extractor = FlowExtractor()
        self.feature_engine = FeatureEngine()
        self.classifier = TrafficClassifier()
        self._results_cache: Dict[str, AnalysisResult] = {}

    def analyze_pcap(
        self,
        filepath: str,
        model_type: str = None,
    ) -> AnalysisResult:
        """
        Run the complete analysis pipeline on a PCAP file.

        Args:
            filepath: Path to PCAP file.
            model_type: ML model to use for classification.

        Returns:
            AnalysisResult with all analysis data.
        """
        start_time = time.time()
        session_id = str(uuid.uuid4())[:8]

        # --- Stage 1: Parse PCAP ---
        packets = self.parser.parse_file(filepath)
        file_info = self.parser.get_file_info()

        # --- Stage 2: Extract Flows ---
        self.flow_extractor.reset()
        for pkt in packets:
            self.flow_extractor.add_packet(pkt)
        self.flow_extractor.finalize()
        flows = self.flow_extractor.get_all_flows()

        # --- Stage 3: Compute Features ---
        flow_features = self.feature_engine.extract_batch(flows)

        # --- Stage 4: Classification ---
        # For demo purposes, use synthetic training data if no model is loaded
        if model_type:
            self.classifier = TrafficClassifier(model_type)

        classified_flows = self._classify_flows(flow_features, flows)

        # --- Stage 5: Aggregate Results ---
        protocol_dist = Counter(f.protocol_name for f in flows)
        class_dist = Counter(r["predicted_class"] for r in classified_flows)

        # Build flow records
        flow_records = []
        for flow, features, classification in zip(flows, flow_features, classified_flows):
            record = flow.to_dict()
            record["predicted_class"] = classification["predicted_class"]
            record["confidence"] = classification["confidence"]
            record["features"] = dict(zip(features.feature_names, features.feature_vector))
            flow_records.append(record)

        processing_time = time.time() - start_time

        result = AnalysisResult(
            session_id=session_id,
            filename=file_info.get("filename", os.path.basename(filepath)),
            file_size=file_info.get("file_size", 0),
            total_packets=file_info.get("total_packets", 0),
            valid_packets=file_info.get("valid_packets", len(packets)),
            total_flows=len(flows),
            classified_flows=len(classified_flows),
            protocol_distribution=dict(protocol_dist),
            class_distribution=dict(class_dist),
            model_type=self.classifier.model_type,
            accuracy=self.classifier.training_metadata.get("accuracy"),
            processing_time=processing_time,
            flow_records=flow_records,
            feature_importance=self.classifier.training_metadata.get(
                "feature_importance", {}
            ),
        )

        self._results_cache[session_id] = result
        return result

    def _classify_flows(
        self, features: List[FlowFeatures], flows: List[Flow]
    ) -> List[Dict]:
        """
        Classify flows using the ML model.

        If no trained model is available, uses heuristic classification
        based on well-known port numbers and traffic patterns.
        """
        if self.classifier.is_trained:
            return self.classifier.predict(features)

        # Heuristic classification based on port numbers and patterns
        return [self._heuristic_classify(flow, feat) for flow, feat in zip(flows, features)]

    def _heuristic_classify(self, flow: Flow, features: FlowFeatures) -> Dict:
        """
        Rule-based heuristic classification using port numbers
        and statistical features.
        """
        port = min(flow.src_port, flow.dst_port)
        feature_dict = dict(zip(features.feature_names, features.feature_vector))

        predicted_class = "unknown"
        confidence = 0.0

        # Port-based rules
        port_rules = {
            (80, 8080, 8443, 3000, 5000): ("web_browsing", 0.75),
            (443,): ("web_browsing", 0.65),  # Could be any HTTPS
            (21, 22, 990, 989): ("file_transfer", 0.85),
            (20, 69): ("file_transfer", 0.80),
            (25, 465, 587, 993, 995, 110, 143): ("email", 0.85),
            (53, 5353): ("dns", 0.90),
            (5060, 5061, 3478, 3479): ("voip", 0.80),
            (1935, 554, 8554): ("video_streaming", 0.75),
        }

        for ports, (cls, conf) in port_rules.items():
            if port in ports:
                predicted_class = cls
                confidence = conf
                break

        # Refine with statistical features
        if predicted_class == "web_browsing" and port == 443:
            duration = feature_dict.get("flow_duration", 0)
            byte_rate = feature_dict.get("flow_byte_rate", 0)
            pkt_ratio = feature_dict.get("fwd_bwd_packet_ratio", 1.0)

            # Video streaming: high byte rate, long duration
            if byte_rate > 100000 and duration > 5:
                predicted_class = "video_streaming"
                confidence = 0.70

            # VoIP: consistent packet rate, small packets
            elif (
                feature_dict.get("pkt_size_variation", 0) < 0.3
                and feature_dict.get("fwd_pkt_size_mean", 0) < 300
                and duration > 2
            ):
                predicted_class = "voip"
                confidence = 0.60

            # Social media: moderate byte rate, bidirectional
            elif 0.5 < pkt_ratio < 2.0 and byte_rate < 50000:
                predicted_class = "social_media"
                confidence = 0.55

        # P2P: multiple connections, both directions roughly equal
        if predicted_class == "unknown" and port > 1024:
            pkt_ratio = feature_dict.get("fwd_bwd_packet_ratio", 0)
            byte_ratio = feature_dict.get("fwd_bwd_byte_ratio", 0)
            if 0.7 < pkt_ratio < 1.4 and 0.7 < byte_ratio < 1.4:
                predicted_class = "p2p"
                confidence = 0.50

        # Gaming: low latency, small packets, low variation
        if predicted_class == "unknown":
            avg_payload = feature_dict.get("avg_payload_size", 0)
            iat_mean = feature_dict.get("fwd_iat_mean", 0)
            if avg_payload < 200 and 0 < iat_mean < 0.05:
                predicted_class = "gaming"
                confidence = 0.55

        # Default
        if predicted_class == "unknown":
            confidence = 0.30

        return {
            "flow_id": flow.flow_id,
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "class_probabilities": {},
        }

    def generate_demo_data(self) -> AnalysisResult:
        """
        Generate synthetic demo data for demonstration purposes.
        Creates realistic-looking analysis results without requiring
        a real PCAP file.
        """
        session_id = str(uuid.uuid4())[:8]
        np.random.seed(42)

        # Synthetic flow data
        categories = [
            "web_browsing", "video_streaming", "file_transfer",
            "voip", "dns", "social_media", "email", "gaming",
        ]
        weights = [0.30, 0.20, 0.10, 0.08, 0.12, 0.10, 0.05, 0.05]

        num_flows = 150
        flow_records = []
        class_distribution = Counter()
        protocol_distribution = Counter()

        sample_ips = [
            "192.168.1.100", "192.168.1.101", "10.0.0.5",
            "172.16.0.10", "192.168.1.200",
        ]
        server_ips = [
            "142.250.190.78", "151.101.1.140", "104.18.32.68",
            "52.84.150.11", "13.107.42.14", "34.107.221.82",
        ]

        for i in range(num_flows):
            cat = random.choices(categories, weights=weights, k=1)[0]
            class_distribution[cat] += 1

            proto = random.choice(["TCP", "UDP"]) if cat != "dns" else "UDP"
            protocol_distribution[proto] += 1

            # Generate realistic port numbers
            if cat == "web_browsing":
                dst_port = random.choice([80, 443])
            elif cat == "video_streaming":
                dst_port = 443
            elif cat == "file_transfer":
                dst_port = random.choice([21, 22])
            elif cat == "voip":
                dst_port = random.choice([5060, 3478])
            elif cat == "dns":
                dst_port = 53
            elif cat == "social_media":
                dst_port = 443
            elif cat == "email":
                dst_port = random.choice([25, 587, 993])
            else:
                dst_port = random.randint(3000, 9000)

            duration = max(0.01, np.random.exponential(scale=5.0))
            total_pkts = max(3, int(np.random.lognormal(mean=3, sigma=1)))
            fwd_pkts = max(1, int(total_pkts * random.uniform(0.3, 0.7)))
            bwd_pkts = total_pkts - fwd_pkts

            total_bytes = int(np.random.lognormal(mean=8, sigma=2))
            fwd_bytes = int(total_bytes * random.uniform(0.2, 0.8))
            bwd_bytes = total_bytes - fwd_bytes

            record = {
                "flow_id": f"flow_{i:04d}",
                "src_ip": random.choice(sample_ips),
                "dst_ip": random.choice(server_ips),
                "src_port": random.randint(49152, 65535),
                "dst_port": dst_port,
                "protocol": proto,
                "duration": round(duration, 4),
                "total_packets": total_pkts,
                "forward_packets": fwd_pkts,
                "backward_packets": bwd_pkts,
                "total_bytes": total_bytes,
                "forward_bytes": fwd_bytes,
                "backward_bytes": bwd_bytes,
                "predicted_class": cat,
                "confidence": round(random.uniform(0.55, 0.98), 4),
                "features": {
                    "fwd_pkt_size_mean": round(fwd_bytes / max(1, fwd_pkts), 2),
                    "bwd_pkt_size_mean": round(bwd_bytes / max(1, bwd_pkts), 2),
                    "flow_byte_rate": round(total_bytes / max(0.01, duration), 2),
                    "flow_packet_rate": round(total_pkts / max(0.01, duration), 2),
                    "pkt_size_variation": round(random.uniform(0.1, 0.9), 4),
                },
            }
            flow_records.append(record)

        result = AnalysisResult(
            session_id=session_id,
            filename="demo_capture.pcap",
            file_size=2_456_789,
            total_packets=4500,
            valid_packets=4320,
            total_flows=num_flows,
            classified_flows=num_flows,
            protocol_distribution=dict(protocol_distribution),
            class_distribution=dict(class_distribution),
            model_type="random_forest",
            accuracy=0.8742,
            processing_time=1.234,
            flow_records=flow_records,
            feature_importance={
                "flow_byte_rate": 0.1523,
                "fwd_pkt_size_mean": 0.1245,
                "bwd_pkt_size_mean": 0.1089,
                "flow_duration": 0.0987,
                "pkt_size_variation": 0.0876,
                "fwd_iat_mean": 0.0765,
                "total_fwd_bytes": 0.0654,
                "avg_payload_size": 0.0598,
                "flow_packet_rate": 0.0543,
                "fwd_bwd_byte_ratio": 0.0432,
                "bwd_iat_mean": 0.0321,
                "total_bwd_bytes": 0.0287,
                "fwd_pkt_size_std": 0.0234,
                "bwd_pkt_size_std": 0.0189,
                "fwd_bwd_packet_ratio": 0.0156,
                "fwd_pkt_size_min": 0.0101,
            },
        )

        self._results_cache[session_id] = result
        return result

    def get_result(self, session_id: str) -> Optional[AnalysisResult]:
        """Get cached analysis result by session ID."""
        return self._results_cache.get(session_id)

    def get_all_sessions(self) -> List[Dict]:
        """Get summaries of all analysis sessions."""
        return [r.summary for r in self._results_cache.values()]
