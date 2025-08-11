**Penguin Classification API**

Welcome to the Penguin Classification API! Deployed at https://penguin-api-191199043596.us-central1.run.app, this project delivers a machine learning application for classifying penguin species using an XGBoost model trained on the Penguins dataset. Built with FastAPI, containerized with Docker, and deployed on Google Cloud Run, it ensures scalable, production-ready inference. The model is stored in Google Cloud Storage and loaded via the Google Cloud SDK. Comprehensive unit tests and Locust load testing validate reliability and performance.

This repository fulfills Assignment 2: Building and Deploying Your ML Application with CI/CD, covering:

1.Testing

2.Containerization

3.Cloud deployment

4.Load testing

 **Features**

-FastAPI Backend: Serves predictions via /predict with Pydantic validation.

-XGBoost Model: Trained on Penguins dataset, stored as JSON in Google Cloud Storage.

-Dockerized Deployment: Optimized Dockerfile, deployed to Cloud Run.

-Unit Testing: Covers model predictions, API endpoints, and edge cases.

-Load Testing: Locust-based tests for scalability and performance.

Setup Instructions

### Prerequisites

- **Google Cloud Account** ([Free trial](https://cloud.google.com/free))
- GCP Project with the following APIs enabled:
  - Cloud Run
  - Artifact Registry
  - Google Cloud Storage
- **Local Development Tools**:
  - [Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Python 3.10.16+ with virtual environment (e.g., `venv` or `uv`)
  - [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) with `gcloud init`
  - `gsutil` for Google Cloud Storage
  - GitHub account with write access to repository
- **Lab 3 Assets**:
  - Trained **XGBoost** model (`model.json`)
  - **FastAPI** app with `/predict` endpoint

---

### 🔹 Installation

1. **Clone Repository**
    ```bash
    git clone https://github.com/<your-username>/<your-repo-name>.git
    cd <your-repo-name>
    ```

2. **Set Up Python Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    uv pip install -r requirements.txt
    ```

3. **Configure Google Cloud**
   - Create service account: `penguin-api-sa`  
     *(IAM & Admin > Service Accounts)*  
     Assign roles:
       - `Storage Object Viewer`
       - `Storage Bucket Viewer`
   - Download key: `sa-key.json`  
     Add to `.gitignore` & `.dockerignore`
   - Create `.env` file:
     ```env
     GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json
     GCS_BUCKET_NAME=<your-bucket-name>
     GCS_BLOB_NAME=<your-model-file.json>
     ```

4. **Build and Test Locally**
    ```bash
    docker build -t penguin-api .
    docker run -d -p 8080:8080 \
      --name penguin-api \
      -v /path/to/sa-key.json:/gcp/sa-key.json:ro \
      -e GOOGLE_APPLICATION_CREDENTIALS=/gcp/sa-key.json \
      penguin-api
    ```

5. **Test `/predict` Endpoint**
    ```bash
    curl -X POST http://localhost:8080/predict \
      -H "Content-Type: application/json" \
      -d '{"bill_length_mm": 39.1, "bill_depth_mm": 18.7, "flipper_length_mm": 181, "body_mass_g": 3750}'
    ```

6. **Run Unit Tests**
    ```bash
    pytest --cov=app tests/
    ```

---

## 🌐 API Documentation

**Base URL (Production):**  
`https://penguin-api-191199043596.us-central1.run.app`

### **Endpoints**
#### `GET /`
- **Description:** Returns welcome message
- **Response:**
  ```json
  {"message": "Hello! Welcome to the Penguins Classification API."}
POST /predict
Description: Predicts penguin species

Request Body:

json
Copy
Edit
{
  "bill_length_mm": float,
  "bill_depth_mm": float,
  "flipper_length_mm": float,
  "body_mass_g": float
}
Response:

json
Copy
Edit
{"prediction": "Adelie"}
Status Codes:

200 OK: Successful prediction

422 Unprocessable Entity: Invalid or missing inputs

📄 Swagger Docs: View here

📊 Test Coverage Report
Command:

bash
Copy
Edit
pytest --cov=. --cov-report=term-missing tests/
| File       | Statements | Missed | Coverage |
|------------|------------|--------|----------|
| main.py    | 151        | 41     | 73%      |
| locust.py  | 0          | 0      | 100%     |
| test.py    | 70         | 7      | 91%      |
| train.py   | 39         | 39     | 0%       |
| **Total**  | **260**    | **86** | **67%**  |


Analysis:

main.py (73%) – Core logic covered, some edge cases missing

test.py (91%) – Well-tested

train.py (0%) – Not required in scope

locust.py (100%) – Covered due to simplicity

🚀 Deployment
Live: Penguin API

See DEPLOYMENT.md for:

Docker image build & push to Artifact Registry

Cloud Run deployment steps

Commands, issues, and fixes

📈 Load Testing
Results are in LOAD_TEST_REPORT.md:

Response times, failure rates, throughput for:

Baseline

Normal load

Stress

Spike

Bottlenecks found & optimization recommendations

**Production Q & A**
1) Edge cases not in training data (what could break it?)

Out-of-distribution inputs (e.g., new island names, sex not in {male,female}, unusual years).

Sensor/unit errors (mm vs cm), negatives/zeros, extreme outliers.

Schema drift (missing fields, renamed keys).

Population shift (species ratios change) causing calibration issues.

2) If the model file is corrupted

Load fails at startup → health reports degraded/Model not ready; predictions return 503.

Mitigate: checksum (MD5/CRC32C) validation, store two versions (active/canary), failover to previous good artifact.

3) Realistic load for a penguin classifier

Typical classroom/demo: 1–20 RPS (requests/sec) peak, ~<1000 req/day.

Comfortable target on Cloud Run single instance (1 CPU): 5–20 RPS with p50 < 100 ms (model is tiny).

4) If responses are too slow—optimizations

Warm start: keep one instance always on (min instances > 0).

Speed up I/O: load model once; cache encoders; avoid per-request disk/GCS work.

Use smaller/quantized model if needed; switch to predictor.predict(DMatrix, validate_features=False) (already used).

Increase CPU/memory; raise concurrency in Cloud Run; batch small bursts if appropriate.

Profile (py-spy), remove pandas if it’s the bottleneck (use NumPy dict→array directly).

5) Most important metrics for ML inference APIs

Latency: p50/p95/p99.

Throughput: RPS.

Error rates: 4xx/5xx, validation failures.

Availability & cold-start count.

Cost per 1k requests.

Model-specific: class distribution, drift signals (optional).

6) Why Docker layer caching matters (and did we use it?)

It reuses unchanged layers to avoid reinstalling deps → much faster builds.

Yes: placing requirements.txt before copying source lets pip install be cached; later code edits don’t bust the deps layer.

7) Risks of running containers as root

Wider blast radius if compromised; filesystem and network changes are easier for an attacker.

Mitigate: run as non-root user, read-only filesystem, minimal base image, drop capabilities, no shell tools you don’t need.

8) How cloud auto-scaling impacts load tests

Short spikes may hit cold starts → higher p95/p99 latency initially.

Sustained load triggers scale-out; latency drops after new instances become warm.

Costs scale with instances; choose sensible min/max instances.

9) What if traffic jumps 10×

Expect brief 5xx or high tail latency during scale-out; throughput normalizes once additional instances spin up.

Prepare with higher max instances, min instances > 0, and lighter model/preprocessing.

10) How to monitor in production

Use Cloud Monitoring/Logging: dashboard p50/p95, RPS, 4xx/5xx, instance count, CPU/RAM.

Synthetic checks to /health.

Structured logs for /predict (timings, validation errors—not PII).

Optional APM (OpenTelemetry) for traces.

11) Blue-green deployment approach

Build new image → deploy as green service revision.

Run smoke tests and a small canary (e.g., 5% traffic).

If healthy, shift 100% traffic to green; keep blue for fast rollback.

12) If a production deployment fails

Roll back traffic to the last good revision (one click in Cloud Run).

Inspect logs, diff env vars, verify artifact versions; fix and redeploy.

Keep a “runbook” with known failure modes and commands.

13) If the container uses too much memory

Cloud Run will OOM-kill the instance; requests may fail intermittently.

Mitigate: raise memory limit, reduce batch size, release large objects, avoid loading unnecessary libs/data, enable memory profiling, control concurrency.

