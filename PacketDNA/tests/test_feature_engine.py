"""
PacketDNA - Feature Engine Unit Tests
"""

import unittest
import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from core.flow_extractor import Flow, Packet
from core.feature_engine import FeatureEngine, FlowFeatures


class TestFeatureEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FeatureEngine()

    def test_extract_features_basic(self):
        flow = Flow(
            flow_id="test_flow_1",
            src_ip="192.168.1.100",
            dst_ip="8.8.8.8",
            src_port=49152,
            dst_port=53,
            protocol=17,
            protocol_name="UDP",
            start_time=1000.0,
            end_time=1000.02,
        )

        p1 = Packet(
            timestamp=1000.0,
            src_ip="192.168.1.100",
            dst_ip="8.8.8.8",
            src_port=49152,
            dst_port=53,
            protocol=17,
            size=80,
            payload_size=52,
            direction=0,
        )
        p2 = Packet(
            timestamp=1000.02,
            src_ip="8.8.8.8",
            dst_ip="192.168.1.100",
            src_port=53,
            dst_port=49152,
            protocol=17,
            size=120,
            payload_size=92,
            direction=1,
        )

        flow.packets = [p1, p2]
        flow.forward_packets = [p1]
        flow.backward_packets = [p2]

        features = self.engine.extract_features(flow)
        self.assertIsNotNone(features)
        self.assertEqual(len(features.feature_vector), 22)
        self.assertEqual(len(features.feature_names), 22)

        feat_dict = features.to_dict()
        self.assertEqual(feat_dict["flow_id"], "test_flow_1")
        self.assertEqual(feat_dict["fwd_pkt_size_mean"], 80.0)
        self.assertEqual(feat_dict["bwd_pkt_size_mean"], 120.0)
        self.assertEqual(feat_dict["total_packets"], 2.0)

    def test_extract_batch(self):
        flow = Flow(
            flow_id="test_flow_2",
            src_ip="10.0.0.1",
            dst_ip="10.0.0.2",
            src_port=1000,
            dst_port=2000,
            protocol=6,
            protocol_name="TCP",
            start_time=100.0,
            end_time=101.0,
        )
        p = Packet(
            timestamp=100.0,
            src_ip="10.0.0.1",
            dst_ip="10.0.0.2",
            src_port=1000,
            dst_port=2000,
            protocol=6,
            size=500,
            payload_size=460,
        )
        flow.packets = [p]
        flow.forward_packets = [p]

        batch = self.engine.extract_batch([flow])
        self.assertEqual(len(batch), 1)
        self.assertEqual(batch[0].flow_id, "test_flow_2")


if __name__ == "__main__":
    unittest.main()
