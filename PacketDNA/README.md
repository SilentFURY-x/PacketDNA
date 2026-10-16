# PacketDNA 🧬

## Intelligent Network Traffic Fingerprinting and Application Classification

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-Academic-purple.svg)]()

> A privacy-preserving network traffic classification system that identifies applications
> from encrypted network flows using statistical fingerprints — no payload inspection required.

---

## 🎯 Overview

PacketDNA classifies network traffic into application categories (web browsing, video streaming, VoIP, etc.) by analyzing **statistical properties** of network flows rather than inspecting packet contents. This approach works even on encrypted traffic (TLS 1.3, QUIC).

### Key Features

- **🔒 Privacy-Preserving** — Works without decrypting or inspecting payloads
- **📐 22 Statistical Features** — Packet sizes, inter-arrival times, byte rates, ratios
- **🤖 ML Classification** — Random Forest, KNN, Decision Tree models
- **📊 Interactive Dashboard** — Real-time visualization with Chart.js
- **📦 PCAP Support** — Upload and analyze PCAP/PCAPNG capture files
- **🌐 REST API** — Complete JSON API for integration

## 🏗️ Architecture

```
PacketDNA/
├── backend/         # Flask API + ML Pipeline
│   ├── core/        # Flow extractor, Feature engine, Classifier
│   ├── api/         # REST API endpoints
│   ├── services/    # Analysis orchestration
│   ├── models/      # Data models
│   └── ml/          # ML training & saved models
├── frontend/        # Interactive Dashboard
│   ├── css/         # Design system + components
│   └── js/          # API client + Chart.js visualizations
└── docs/            # PRD, Demo Guide, LaTeX Report
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
cd PacketDNA/backend
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

### Demo

Click **"Run Demo Analysis"** on the dashboard to see the system in action with synthetic data.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/demo` | Generate demo analysis |
| POST | `/api/v1/analyze` | Upload & analyze PCAP |
| GET | `/api/v1/results/:id` | Get analysis results |
| GET | `/api/v1/sessions` | List all sessions |
| GET | `/api/v1/stats` | System statistics |

## 📐 Feature Engineering

PacketDNA extracts 22 statistical features organized into 4 categories:

1. **Packet Size Statistics** — Mean, std, min, max for forward/backward streams
2. **Inter-Arrival Time** — Mean, std for forward/backward IAT
3. **Flow Aggregates** — Duration, byte rate, packet rate, total bytes
4. **Ratio Features** — Fwd/bwd ratios, payload averages, coefficient of variation

## 📄 Documentation

- [Product Requirements Document](docs/PRD.md)
- [Simple Project Explanation](docs/SIMPLE_EXPLANATION.md)
- [Demo Guide](docs/DEMO_GUIDE.md)
- [Academic Report](docs/report/main.tex)

## 🔬 References

1. Moore & Zuev (2005). "Internet Traffic Classification Using Bayesian Analysis." ACM SIGMETRICS.
2. Nguyen & Armitage (2008). "A Survey of Techniques for Internet Traffic Classification." IEEE COMST.
3. Dainotti et al. (2012). "Issues and Future Directions in Traffic Classification." IEEE Network.

---

*Computer Networks Course Project — 3rd Year B.Sc. Computer Science*
