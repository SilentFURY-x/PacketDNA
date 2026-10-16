"""
PacketDNA - ML Classifier Unit Tests
"""

import unittest
import sys
import os
import random
import numpy as np

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from core.classifier import TrafficClassifier
from core.feature_engine import FlowFeatures, FeatureEngine


class TestClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = TrafficClassifier(model_type="random_forest")
        self.feature_names = FeatureEngine.FEATURE_NAMES

    def _generate_mock_dataset(self, samples_per_class=20):
        classes = ["web_browsing", "video_streaming", "voip", "dns"]
        features_list = []
        random.seed(42)
        np.random.seed(42)

        for cat in classes:
            for i in range(samples_per_class):
                # Differentiate feature vectors per class
                if cat == "video_streaming":
                    vec = [random.uniform(1100, 1450)] * 4 + [random.uniform(50, 100)] * 4 + [random.uniform(0.01, 0.04)] * 4 + [10.0, 50000.0, 100.0, 500000.0, 5000.0, 200.0, 0.9, 0.95, 1200.0, 0.1]
                elif cat == "voip":
                    vec = [random.uniform(150, 250)] * 4 + [random.uniform(150, 250)] * 4 + [0.02] * 4 + [5.0, 8000.0, 50.0, 20000.0, 20000.0, 100.0, 0.5, 0.5, 160.0, 0.05]
                elif cat == "dns":
                    vec = [random.uniform(60, 90)] * 4 + [random.uniform(80, 150)] * 4 + [0.01] * 4 + [0.05, 1200.0, 20.0, 100.0, 150.0, 2.0, 0.5, 0.4, 70.0, 0.2]
                else:  # web_browsing
                    vec = [random.uniform(400, 900)] * 4 + [random.uniform(300, 700)] * 4 + [random.uniform(0.05, 0.2)] * 4 + [2.0, 15000.0, 30.0, 10000.0, 8000.0, 20.0, 0.6, 0.55, 600.0, 0.4]

                # Ensure vector is exactly 22 dimensions
                vec = (vec + [0.0] * 22)[:22]
                features_list.append(FlowFeatures(
                    flow_id=f"flow_{cat}_{i}",
                    feature_vector=vec,
                    feature_names=self.feature_names,
                    label=cat
                ))
        return features_list

    def test_train_and_predict(self):
        dataset = self._generate_mock_dataset(samples_per_class=20)
        metrics = self.classifier.train(dataset, test_size=0.25)

        self.assertTrue(self.classifier.is_trained)
        self.assertIn("accuracy", metrics)
        self.assertGreaterEqual(metrics["accuracy"], 0.70)
        self.assertIn("feature_importance", metrics)

        # Test prediction
        test_samples = [dataset[0], dataset[25]]
        predictions = self.classifier.predict(test_samples)

        self.assertEqual(len(predictions), 2)
        self.assertIn("predicted_class", predictions[0])
        self.assertIn("confidence", predictions[0])
        self.assertGreater(predictions[0]["confidence"], 0.0)

    def test_unsupported_model_raises_value_error(self):
        with self.assertRaises(ValueError):
            TrafficClassifier(model_type="invalid_model_xyz")


if __name__ == "__main__":
    unittest.main()
