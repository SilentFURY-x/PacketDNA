"""
PacketDNA - ML Classifier Module
==================================
Machine learning classifier for network traffic classification.

Supports multiple algorithms:
    - Random Forest (default, best overall performance)
    - K-Nearest Neighbors
    - Decision Tree

Uses scikit-learn for model training and inference.
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
)

from config.settings import get_config
from core.feature_engine import FlowFeatures

config = get_config()


class TrafficClassifier:
    """
    ML-based network traffic classifier.

    Classifies network flows into application categories based on
    their statistical feature vectors. Supports training, evaluation,
    prediction, and model persistence.

    Attributes:
        model_type: Type of ML model ('random_forest', 'knn', 'decision_tree')
        model: The trained scikit-learn classifier
        scaler: Feature standardization scaler
        label_encoder: Label encoder for class names
    """

    SUPPORTED_MODELS = {
        "random_forest": "Random Forest",
        "knn": "K-Nearest Neighbors",
        "decision_tree": "Decision Tree",
    }

    # Default application categories for traffic classification
    TRAFFIC_CATEGORIES = [
        "web_browsing",
        "video_streaming",
        "file_transfer",
        "voip",
        "gaming",
        "email",
        "vpn",
        "p2p",
        "social_media",
        "cloud_storage",
        "dns",
        "unknown",
    ]

    def __init__(self, model_type: str = None):
        self.model_type = model_type or config.DEFAULT_MODEL
        if self.model_type not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {self.model_type}. "
                f"Choose from: {list(self.SUPPORTED_MODELS.keys())}"
            )

        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self._is_trained = False
        self._training_metadata = {}

    def _create_model(self):
        """Create a new model instance based on model_type."""
        if self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=config.N_ESTIMATORS,
                random_state=config.RANDOM_STATE,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                n_jobs=-1,
            )
        elif self.model_type == "knn":
            self.model = KNeighborsClassifier(
                n_neighbors=5,
                weights="distance",
                metric="minkowski",
                n_jobs=-1,
            )
        elif self.model_type == "decision_tree":
            self.model = DecisionTreeClassifier(
                random_state=config.RANDOM_STATE,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
            )

    def train(
        self,
        features: List[FlowFeatures],
        test_size: float = None,
    ) -> Dict:
        """
        Train the classifier on labeled flow features.

        Args:
            features: List of FlowFeatures with labels.
            test_size: Fraction of data for testing (0-1).

        Returns:
            Dictionary containing training results and metrics.
        """
        if not features:
            raise ValueError("No features provided for training")

        test_size = test_size or config.TEST_SPLIT_RATIO

        # Prepare data
        X = np.array([f.feature_vector for f in features])
        labels = [f.label or "unknown" for f in features]
        y = self.label_encoder.fit_transform(labels)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y,
            test_size=test_size,
            random_state=config.RANDOM_STATE,
            stratify=y if len(set(y)) > 1 else None,
        )

        # Create and train model
        self._create_model()
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average="weighted", zero_division=0
        )

        # Per-class metrics
        class_names = self.label_encoder.classes_
        report = classification_report(
            y_test, y_pred,
            target_names=class_names,
            output_dict=True,
            zero_division=0,
        )

        # Cross-validation score
        cv_scores = cross_val_score(
            self.model, X_scaled, y, cv=min(5, len(set(y))), scoring="accuracy"
        )

        self._is_trained = True
        self._training_metadata = {
            "model_type": self.model_type,
            "model_name": self.SUPPORTED_MODELS[self.model_type],
            "trained_at": datetime.now().isoformat(),
            "total_samples": len(features),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "num_classes": len(class_names),
            "class_names": class_names.tolist(),
            "num_features": X.shape[1],
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "cv_mean_accuracy": round(cv_scores.mean(), 4),
            "cv_std_accuracy": round(cv_scores.std(), 4),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "classification_report": report,
        }

        # Feature importance (for tree-based models)
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            feature_names = features[0].feature_names
            importance_dict = dict(zip(feature_names, importances.tolist()))
            # Sort by importance
            importance_dict = dict(
                sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
            )
            self._training_metadata["feature_importance"] = importance_dict

        return self._training_metadata

    def predict(self, features: List[FlowFeatures]) -> List[Dict]:
        """
        Predict traffic categories for flow features.

        Args:
            features: List of FlowFeatures (unlabeled).

        Returns:
            List of prediction results with confidence scores.
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call train() first or load a model.")

        X = np.array([f.feature_vector for f in features])
        X_scaled = self.scaler.transform(X)

        predictions = self.model.predict(X_scaled)
        pred_labels = self.label_encoder.inverse_transform(predictions)

        # Get probability estimates if available
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(X_scaled)
        else:
            probabilities = None

        results = []
        for i, (feature, label) in enumerate(zip(features, pred_labels)):
            result = {
                "flow_id": feature.flow_id,
                "predicted_class": label,
            }

            if probabilities is not None:
                class_probs = dict(
                    zip(
                        self.label_encoder.classes_.tolist(),
                        [round(p, 4) for p in probabilities[i].tolist()],
                    )
                )
                result["confidence"] = round(float(max(probabilities[i])), 4)
                result["class_probabilities"] = class_probs
            else:
                result["confidence"] = 1.0
                result["class_probabilities"] = {}

            results.append(result)

        return results

    def save_model(self, filepath: str = None):
        """Save trained model, scaler, and encoder to disk."""
        if not self._is_trained:
            raise RuntimeError("No trained model to save.")

        if filepath is None:
            os.makedirs(config.ML_MODELS_DIR, exist_ok=True)
            filepath = os.path.join(
                config.ML_MODELS_DIR, f"{self.model_type}_model.pkl"
            )

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "label_encoder": self.label_encoder,
            "metadata": self._training_metadata,
        }
        joblib.dump(model_data, filepath)

        # Save metadata as JSON
        meta_path = filepath.replace(".pkl", "_metadata.json")
        # Convert numpy types for JSON serialization
        serializable_meta = self._make_serializable(self._training_metadata)
        with open(meta_path, "w") as f:
            json.dump(serializable_meta, f, indent=2)

        return filepath

    def load_model(self, filepath: str = None):
        """Load a trained model from disk."""
        if filepath is None:
            filepath = os.path.join(
                config.ML_MODELS_DIR, f"{self.model_type}_model.pkl"
            )

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        model_data = joblib.load(filepath)
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.label_encoder = model_data["label_encoder"]
        self._training_metadata = model_data.get("metadata", {})
        self._is_trained = True

    @staticmethod
    def _make_serializable(obj):
        """Convert numpy types to native Python types for JSON serialization."""
        if isinstance(obj, dict):
            return {k: TrafficClassifier._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [TrafficClassifier._make_serializable(v) for v in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    @property
    def is_trained(self) -> bool:
        """Whether the model has been trained."""
        return self._is_trained

    @property
    def training_metadata(self) -> Dict:
        """Training metadata and metrics."""
        return self._training_metadata
