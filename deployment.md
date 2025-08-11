# DEPLOYMENT.md

## Containerization and Deployment Steps

### 1. Dockerfile and .dockerignore

* **Dockerfile** uses `python:3.11-slim` base image.
* Installs dependencies from `requirements.txt` without cache
* Runs FastAPI app via Uvicorn.

### 2. Build and Run Locally

# Build the Docker image
docker build -t penguin-api .

# Run the container mapping host port 8080 to container port 8080
docker run -d --name penguin-api `
  -p 8080:8080 `
  -e GCS_BUCKET_NAME="penguin-model" `
  -e GCS_BLOB_NAME="model.json" `
  -e GOOGLE_APPLICATION_CREDENTIALS="/gcp/sa-key.json" `
  -v "${PWD}\secrets\sa-key.json:/gcp/sa-key.json:ro" `
  penguin-api:latest

```

### 3. Testing Endpoints (locally)

```bash
# Health checkcurl http://localhost:8080/health
# ⇒ {"status":"ok"}

# Root endpoint
 http://localhost:8080/
# ⇒ {"message":"Hello! Welcome to the Penguins Classification API."}

# Prediction endpoint (PowerShell)
$body = '{"bill_length_mm":40.0,"bill_depth_mm":18.0,"flipper_length_mm":195,"body_mass_g":4000,"year":2008,"sex":"male","island":"Biscoe"}'
Invoke-RestMethod -Uri http://localhost:8080/predict -Method POST -Body $body -ContentType 'application/json'
# ⇒ {"species":"Adelie"}
```

### 4. Issues Encountered and Solutions

Model mismatch error in Cloud Run → caused by old model artifacts → fixed by re-training and uploading fresh model.json & encoders.json.

Port 8080 already in use → caused by previous container running → fixed by stopping old container before re-running.

### 5. Performance and Security Observations

* **Image Size**:1.8GB
* **Layers**: 11 layers 


### 6. Summary of Image Layers & Size
```

* **Total Layers**: 11 layers

* **Image Size**: 1.8GB

#  Penguin API Deployment Guide

## 7. Service Account & Environment Variables

###
GOOGLE_APPLICATION_CREDENTIALS=secrets/sa-key.json
GCS_BUCKET_NAME=penguin-model
GCS_MODEL_BLOB=model.json
```

## 8. Google Cloud Deployment

### 8.1. Build for Cloud Run (linux/amd64)
docker build --platform linux/amd64 -t penguin-api .

### 8.2. Tag for Artifact Registry
docker tag penguin-api:latest us-central1-docker.pkg.dev/ml-deployment-demo-467801/penguin-api-repo/penguin-api:latest

docker push us-central1-docker.pkg.dev/ml-deployment-demo-467801/penguin-api-repo/penguin-api:latest


### 8.3. Deploy to Cloud Run

## 8.4. Run & Test

### Health Check

curl https://penguin-api-191199043596.us-central1.run.app
# Response: {"status":"ok"}
```

### Prediction Request
 -X POST https://penguin-api-191199043596.us-central1.run.app/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"bill_length_mm\":40.0,\"bill_depth_mm\":18.0,\"flipper_length_mm\":195,\"body_mass_g\":4000,\"year\":2008,\"sex\":\"male\",\"island\":\"Biscoe\"}"
# Response: {"species":"Adelie"}
```

---

## 9. Deployment Issues & Fixes

-  **Permissions/mount issues**: Fixed volume path and file existence
-  **Cold start delay**: ~10 seconds to load model from GCS
-  **Missing env vars**: Set correctly via Cloud Run UI

---

## 10. Performance

- Cold start: `< 10s`
- Warm prediction: `< 1s`
- Concurrency: Suitable for classroom load

---

## 11. Public URL

```text
https://penguin-api-191199043596.us-central1.run.app
```
