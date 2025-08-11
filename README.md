Penguin Classification API
Project Overview
Welcome to the Penguin Classification API! This project, accessible at https://penguin-api-191199043596.us-central1.run.app, implements a machine learning application for classifying penguin species using an XGBoost model trained on the Penguins dataset. The application is built with FastAPI, containerized using Docker, and deployed to Google Cloud Run for scalable, production-ready inference. The model is stored in Google Cloud Storage and loaded during inference using the Google Cloud SDK. Comprehensive unit tests ensure reliability, and load testing with Locust validates performance under production-scale traffic.
This repository fulfills the requirements of Assignment 2: Building and Deploying Your ML Application with CI/CD, covering testing, containerization, cloud deployment, and load testing. Note that CI/CD pipelines are not implemented in this assignment, as specified, but are prepared for the final project.
Features

FastAPI Application: Serves predictions via a /predict endpoint, with input validation using Pydantic.
XGBoost Model: Trained on the Penguins dataset and stored in Google Cloud Storage as a JSON file.
Dockerized Deployment: Containerized with a production-ready Dockerfile, optimized for performance and security.
Cloud Run Deployment: Deployed to Google Cloud Run at https://penguin-api-191199043596.us-central1.run.app for serverless inference.
Unit Testing: Comprehensive test suite covering model predictions, API endpoints, input validation, and edge cases.
Load Testing: Simulated production traffic using Locust to analyze scalability and performance.
Documentation: Detailed setup instructions, deployment process (DEPLOYMENT.md), and load test analysis (LOAD_TEST_REPORT.md).

Setup Instructions
Prerequisites

Google Cloud Account: Create a free trial account here. Set up a GCP project and enable APIs for Cloud Run, Artifact Registry, and Google Cloud Storage.
Local Development:
Install Docker Desktop.
Install Python 3.10.16+ and set up a virtual environment (e.g., using uv).
Install Google Cloud SDK and authenticate with gcloud init.
Install gsutil for Google Cloud Storage interaction.


GitHub: Clone this repository and ensure you have write access for pushing changes.
Lab 3 Completion: Ensure you have a trained XGBoost model saved as a JSON file and a basic FastAPI app with a /predict endpoint.

Installation

Clone the Repository:
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>


Set Up Python Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
uv pip install -r requirements.txt


Configure Google Cloud:

Create a service account in GCP Console (IAM & Admin > Service Accounts) named penguin-api-sa with roles Storage Object Viewer and Storage Bucket Viewer.
Download the service account key (e.g., sa-key.json) and store it securely. Add it to .gitignore and .dockerignore.
Set environment variables in a .env file:GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json
GCS_BUCKET_NAME=<your-bucket-name>
GCS_BLOB_NAME=<your-model-file.json>




Build and Test Locally:

Build the Docker image:docker build -t penguin-api .


Run the container locally:docker run -d -p 8080:8080 --name penguin-api -v /path/to/sa-key.json:/gcp/sa-key.json:ro -e GOOGLE_APPLICATION_CREDENTIALS=/gcp/sa-key.json penguin-api


Test the /predict endpoint:curl -X POST http://localhost:8080/predict -H "Content-Type: application/json" -d '{"bill_length_mm": 39.1, "bill_depth_mm": 18.7, "flipper_length_mm": 181, "body_mass_g": 3750}'




Run Unit Tests:
pytest --cov=app tests/


Check the coverage report to ensure comprehensive testing.



API Documentation
The Penguin Classification API provides a simple interface for predicting penguin species. Access it at https://penguin-api-191199043596.us-central1.run.app. The API welcomes you with the message: "Hello! Welcome to the Penguins Classification API."

GET / (Root Endpoint)
Description: Returns a welcome message.
Response (JSON):{"message": "Hello! Welcome to the Penguins Classification API."}


Status Code: 200 OK


POST /predict
Description: Predicts penguin species based on input features.
Request Body (JSON):{
  "bill_length_mm": float,
  "bill_depth_mm": float,
  "flipper_length_mm": float,
  "body_mass_g": float
}


Response (JSON):{
  "prediction": "Adelie"
}


Status Codes:
200 OK: Successful prediction.
422 Unprocessable Entity: Invalid or missing input data.


Interactive Docs: Access at https://penguin-api-191199043596.us-central1.run.app/docs.



Test Coverage Report
The test suite was run with the following command:
pytest --cov=. --cov-report=term-missing tests/

Coverage Output:
Name          Stmts   Miss  Cover
--------------------------------
main.py       151     41    73%
locust.py       0      0   100%
test.py        70      7    91%
train.py       39     39     0%
--------------------------------
Total         260     86    67%


Analysis: The test suite achieves 67% overall coverage. main.py (73%) covers most API and model logic but misses some edge cases. test.py (91%) is well-tested, while train.py (0%) lacks tests as it was not required for this assignment. locust.py has 100% coverage due to its simplicity. Future improvements will focus on increasing coverage for main.py and adding tests for train.py.

Deployment
The application is deployed to Google Cloud Run at https://penguin-api-191199043596.us-central1.run.app. Detailed deployment instructions are in DEPLOYMENT.md, covering:

Building and pushing the Docker image to Artifact Registry.
Deploying to Cloud Run via GCP Console.
Commands, issues encountered, and the final Cloud Run URL.

Load Testing
Load test results and analysis are in LOAD_TEST_REPORT.md, including:

Response times, failure rates, and throughput for baseline, normal, stress, and spike scenarios.
Identified bottlenecks and optimization recommendations.

Answers to Assignment Questions

Edge cases not in training data (what could break it?)

Out-of-distribution inputs (e.g., new island names, sex not in {male, female}, unusual years).
Sensor/unit errors (mm vs cm), negatives/zeros, extreme outliers.
Schema drift (missing fields, renamed keys).
Population shift (species ratios change) causing calibration issues.


If the model file is corrupted

Load fails at startup → health reports degraded/Model not ready; predictions return 503.
Mitigate: checksum (MD5/CRC32C) validation, store two versions (active/canary), failover to previous good artifact.


Realistic load for a penguin classifier

Typical classroom/demo: 1–20 RPS (requests/sec) peak, ~<1000 req/day.
Comfortable target on Cloud Run single instance (1 CPU): 5–20 RPS with p50 < 100 ms (model is tiny).


If responses are too slow—optimizations

Warm start: keep one instance always on (min instances > 0).
Speed up I/O: load model once; cache encoders; avoid per-request disk/GCS work.
Use smaller/quantized model if needed; switch to predictor.predict(DMatrix, validate_features=False) (already used).
Increase CPU/memory; raise concurrency in Cloud Run; batch small bursts if appropriate.
Profile (py-spy), remove pandas if it’s the bottleneck (use NumPy dict→array directly).


Most important metrics for ML inference APIs

Latency: p50/p95/p99.
Throughput: RPS.
Error rates: 4xx/5xx, validation failures.
Availability & cold-start count.
Cost per 1k requests.
Model-specific: class distribution, drift signals (optional).


Why Docker layer caching matters (and did we use it?)

It reuses unchanged layers to avoid reinstalling deps → much faster builds.
Yes: placing requirements.txt before copying source lets pip install be cached; later code edits don’t bust the deps layer.


Risks of running containers as root

Wider blast radius if compromised; filesystem and network changes are easier for an attacker.
Mitigate: run as non-root user, read-only filesystem, minimal base image, drop capabilities, no shell tools you don’t need.


How cloud auto-scaling impacts load tests

Short spikes may hit cold starts → higher p95/p99 latency initially.
Sustained load triggers scale-out; latency drops after new instances become warm.
Costs scale with instances; choose sensible min/max instances.


What if traffic jumps 10×

Expect brief 5xx or high tail latency during scale-out; throughput normalizes once additional instances spin up.
Prepare with higher max instances, min instances > 0, and lighter model/preprocessing.


How to monitor in production

Use Cloud Monitoring/Logging: dashboard p50/p95, RPS, 4xx/5xx, instance count, CPU/RAM.
Synthetic checks to /health.
Structured logs for /predict (timings, validation errors—not PII).
Optional APM (OpenTelemetry) for traces.


Blue-green deployment approach

Build new image → deploy as green service revision.
Run smoke tests and a small canary (e.g., 5% traffic).
If healthy, shift 100% traffic to green; keep blue for fast rollback.


If a production deployment fails

Roll back traffic to the last good revision (one click in Cloud Run).
Inspect logs, diff env vars, verify artifact versions; fix and redeploy.
Keep a “runbook” with known failure modes and commands.


If the container uses too much memory

Cloud Run will OOM-kill the instance; requests may fail intermittently.
Mitigate: raise memory limit, reduce batch size, release large objects, avoid loading unnecessary libs/data, enable memory profiling, control concurrency.



Repository Structure
├── app/                    # FastAPI application code
│   ├── main.py             # Main FastAPI app with /predict endpoint
│   ├── model.py            # Model loading and inference logic
├── tests/                  # Unit tests
│   ├── test_api.py         # Tests for API endpoints and model
├── Dockerfile              # Docker configuration
├── .dockerignore           # Files to exclude from Docker build
├── .gitignore              # Files to exclude from Git
├── requirements.txt        # Python dependencies
├── locustfile.py           # Load testing configuration
├── DEPLOYMENT.md           # Deployment process documentation
├── LOAD_TEST_REPORT.md     # Load test results and analysis
├── README.md               # This file

Contributing
This project is for educational purposes. Contributions for bug fixes or improvements are welcome via pull requests with clear descriptions.
License
This project is licensed under the MIT License.
