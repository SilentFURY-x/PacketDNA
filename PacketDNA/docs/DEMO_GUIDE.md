# PacketDNA — Demonstration Guide 🚀

This guide provides step-by-step instructions for running, testing, and presenting the **PacketDNA** network traffic classification platform for course evaluations and project reviews.

---

## 1. Prerequisites & Environment Setup

### System Requirements:
- Python 3.10, 3.11, or 3.12 (Recommended: Python 3.12)
- Any modern web browser (Chrome, Edge, Firefox, Safari)
- Windows, macOS, or Linux

### Dependencies Installed:
- `flask`, `flask-cors`: Web server and REST API
- `scikit-learn`, `numpy`, `scipy`: Machine learning classification pipeline
- `scapy`: Packet capture decoding and analysis

---

## 2. Quick Start: Launching the Application

Open a terminal or PowerShell prompt in the project root:

```bash
cd c:\PROJECTS\NETWORKS\PacketDNA\backend
py -3.12 app.py
```

You should see output similar to:

```
============================================================
  PacketDNA v0.3.0
  Intelligent Network Traffic Classification
============================================================
  Dashboard:  http://127.0.0.1:5000
  API:        http://127.0.0.1:5000/api/v1
  Health:     http://127.0.0.1:5000/api/v1/health
============================================================
 * Running on http://127.0.0.1:5000
```

Now open your web browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 3. Recommended Live Demo Walkthrough (5-Minute Script)

### Step 1: Dashboard Overview & Live Architecture (1 Minute)
- **What to show**: The initial dashboard screen.
- **Talking point**: 
  > *"PacketDNA is designed for the modern encrypted web (TLS 1.3/QUIC). Instead of performing obsolete payload inspection, PacketDNA uses Layer 3/Layer 4 statistical telemetry: packet inter-arrival times, packet length moments, and bidirectional volume ratios."*

### Step 2: Instant Demo Analysis (1 Minute)
- **What to do**: Click the **"Load Demo Analysis"** button in the header or welcome card.
- **What happens**:
  - The frontend calls `/api/v1/demo`.
  - The backend generates 150 simulated bidirectional flows spanning 8 major application classes (`video_streaming`, `voip`, `web_browsing`, `dns`, `file_transfer`, `social_media`, `email`, `gaming`).
  - The dashboard updates in real time with smooth animations:
    - **KPI Metrics**: Total Flows (150), Packets Analyzed (4,500+), Byte Volume (2.4 MB), Classification Accuracy (87.4%).
    - **Traffic Category Breakdown**: Interactive doughnut chart displaying class distribution.
    - **Protocol Distribution**: Bar chart comparing TCP vs. UDP traffic.
    - **Top Feature Importance**: Bar chart highlighting the most influential statistical discriminators (e.g., `flow_byte_rate`, `fwd_pkt_size_mean`, `fwd_iat_mean`).

### Step 3: Interactive Flow Inspection Table (1.5 Minutes)
- **What to do**:
  - Scroll down to the **"Bidirectional Flows"** table.
  - Type `video_streaming` or `voip` into the table filter search bar.
  - Click on any flow row to open the **Flow Detail Modal**.
- **Talking points**:
  > *"Notice how the 5-tuple canonical hashing unites forward and reverse packets into a single conversation. In the detail modal, we can inspect both forward and backward packet size means, inter-arrival jitter, and confidence scores from our Random Forest model."*

### Step 4: Machine Learning Model Comparison (1 Minute)
- **What to do**: Click **"ML Models"** in the sidebar navigation.
- **What to show**:
  - The model selection card comparing **Random Forest**, **K-Nearest Neighbors (KNN)**, and **Decision Tree**.
  - Accuracy, precision, recall, and cross-validation metrics.
  - The feature importance bar breakdown illustrating why statistical flow dynamics distinguish video streaming from VoIP.

### Step 5: PCAP Upload & Real-Time Parsing (0.5 Minutes)
- **What to do**: Click **"Analyze PCAP"** in the sidebar navigation.
- **What to show**:
  - The drag-and-drop file upload area.
  - Explain that users can capture `.pcap` files with Wireshark or `tcpdump` and drop them directly into PacketDNA for offline classification.

---

## 4. Testing REST API Endpoints via Command Line

You can also demonstrate the headless REST API using `curl` or PowerShell:

### 1. Health Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/health"
```
**Expected Response:**
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "classifier_ready": true
}
```

### 2. Run Synthetic Demo Pipeline
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/demo"
```

### 3. Query ML Model Metadata
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/models"
```

---

## 5. Running the Automated Unit Test Suite

To prove code quality and module correctness to the evaluator:

```bash
cd c:\PROJECTS\NETWORKS\PacketDNA
py -3.12 -m unittest discover -s tests -p "test_*.py" -v
```

All 7 test cases will execute and verify:
1. `test_single_packet_flow_creation`: Canonical flow key hashing.
2. `test_bidirectional_flow_pairing`: Forward and backward packet stream pairing.
3. `test_flow_finalization`: Complete flow aggregation.
4. `test_extract_features_basic`: 22 statistical feature extractions.
5. `test_extract_batch`: Batch flow feature transformation.
6. `test_train_and_predict`: Random Forest training and inference.
7. `test_unsupported_model_raises_value_error`: Defensive exception handling.

---

## 6. Troubleshooting

- **Port 5000 in use?**
  Change the port in `backend/app.py` line 83 or set environment variable `PORT=5050`.
- **Numpy/Scikit-learn warning?**
  Ensure you are launching with Python 3.12 (`py -3.12 app.py`), which has stable binary wheels installed.
