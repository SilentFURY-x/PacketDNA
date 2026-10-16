"""
PacketDNA Configuration Settings
================================
Central configuration for the PacketDNA application.
"""

import os


class Config:
    """Base configuration class."""

    # Application
    APP_NAME = "PacketDNA"
    APP_VERSION = "0.3.0"
    DEBUG = False
    TESTING = False

    # Paths
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    SAMPLE_DIR = os.path.join(DATA_DIR, "sample")
    UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
    ML_MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
    DB_PATH = os.path.join(DATA_DIR, "packetdna.db")

    # Upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload
    ALLOWED_EXTENSIONS = {"pcap", "pcapng", "cap"}

    # Flow extraction settings
    FLOW_TIMEOUT = 120  # seconds - idle timeout for flow expiry
    MIN_PACKETS_PER_FLOW = 3  # minimum packets to consider a valid flow

    # Feature extraction settings
    NUM_FEATURES = 22  # number of statistical features per flow
    FIRST_N_PACKETS = 10  # first N packets for fingerprinting

    # ML settings
    DEFAULT_MODEL = "random_forest"
    TEST_SPLIT_RATIO = 0.2
    RANDOM_STATE = 42
    N_ESTIMATORS = 100  # Random Forest trees

    # API settings
    API_PREFIX = "/api/v1"
    CORS_ORIGINS = ["*"]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DB_PATH = ":memory:"


# Configuration mapping
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(env=None):
    """Get configuration based on environment."""
    if env is None:
        env = os.getenv("PACKETDNA_ENV", "development")
    return config_map.get(env, DevelopmentConfig)()
