"""
PacketDNA - Flow Extractor Unit Tests
"""

import unittest
import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from core.flow_extractor import FlowExtractor, Flow, Packet


class TestFlowExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = FlowExtractor(timeout=15.0, min_packets=1)

    def test_single_packet_flow_creation(self):
        pkt = Packet(
            timestamp=100.0,
            src_ip="192.168.1.10",
            dst_ip="142.250.190.46",
            src_port=54321,
            dst_port=443,
            protocol=6,
            size=1200,
            payload_size=1146,
            flags=0x18,  # PSH, ACK
        )
        flow_key = self.extractor.add_packet(pkt)
        self.assertIsNotNone(flow_key)
        self.assertIn(flow_key, self.extractor.active_flows)

        flow = self.extractor.active_flows[flow_key]
        self.assertEqual(flow.total_packets, 1)
        self.assertEqual(flow.total_bytes, 1200)
        self.assertEqual(len(flow.forward_packets) + len(flow.backward_packets), 1)

    def test_bidirectional_flow_pairing(self):
        # Forward packet (client to server)
        p1 = Packet(
            timestamp=100.0,
            src_ip="192.168.1.10",
            dst_ip="142.250.190.46",
            src_port=54321,
            dst_port=443,
            protocol=6,
            size=64,
            payload_size=0,
            flags=0x02,  # SYN
        )
        key1 = self.extractor.add_packet(p1)

        # Reverse packet (server response to client)
        p2 = Packet(
            timestamp=100.05,
            src_ip="142.250.190.46",
            dst_ip="192.168.1.10",
            src_port=443,
            dst_port=54321,
            protocol=6,
            size=64,
            payload_size=0,
            flags=0x12,  # SYN, ACK
        )
        key2 = self.extractor.add_packet(p2)

        self.assertEqual(key1, key2)
        flow = self.extractor.active_flows[key1]
        self.assertEqual(flow.total_packets, 2)
        self.assertEqual(len(flow.forward_packets), 1)
        self.assertEqual(len(flow.backward_packets), 1)
        self.assertEqual(flow.total_bytes, 128)
        self.assertAlmostEqual(flow.duration, 0.05, places=3)

    def test_flow_finalization(self):
        p1 = Packet(
            timestamp=100.0,
            src_ip="10.0.0.1",
            dst_ip="10.0.0.2",
            src_port=1234,
            dst_port=80,
            protocol=6,
            size=100,
            payload_size=46,
        )
        self.extractor.add_packet(p1)
        self.extractor.finalize()
        all_flows = self.extractor.get_all_flows()
        self.assertGreaterEqual(len(all_flows), 1)


if __name__ == "__main__":
    unittest.main()
