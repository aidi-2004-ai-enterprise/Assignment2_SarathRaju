# LOAD_TEST_REPORT.md

## Project Details
- **Project ID:** Assignment2_SarathRaju
- **API URL:** https://penguin-api-iuhex5z56a-pd.a.run.app
- **Endpoint Tested:** POST `/predict`
- **Model:** XGBoost Classifier (Penguin species prediction)
- **Deployment:** Google Cloud Run (Containerized FastAPI app)

---

## 1. Test Scenarios & Results

### **Scenario A — Baseline Load**
**Setup:** 10 users, 5 minutes  
**Results:**
- **Total Requests:** 1,458
- **Throughput (RPS):** 4.9
- **Failures:** 0 (0%)
- **Latency (ms):**
  - Median: 22
  - p95: 30
  - p99: 40
  - Min: 17
  - Max: 96
  - Average: 23.16
- **Observation:** Stable latency and zero failures under light load.

---

### **Scenario B — Normal Load**
**Setup:** 25 users, 3 minutes  
**Results:**
- **Total Requests:** 2,362
- **Throughput (RPS):** 23.7
- **Failures:** 0 (0%)
- **Latency (ms):**
  - Median: 23
  - p95: 52
  - p99: 77
  - Min: 17
  - Max: 115
  - Average: 27.26
- **Observation:** Minor increase in p95 and p99 latency, still no failures.

---

### **Scenario C — Stress Test**
**Setup:** 50 users, 2 minutes  
**Results:**
- **Total Requests:** 4,702
- **Throughput (RPS):** ~39.2
- **Failures:** 0 (0%)
- **Latency (ms):**
  - Median: 25
  - p95: 59
  - p99: 98
  - Min: 18
  - Max: 124
  - Average: 31.1
- **Observation:** Slight rise in latency under heavier sustained load, but still within acceptable limits.

---

### **Scenario D — Spike Test**
**Setup:** Ramp from 1 to 100 users in 1 minute  
**Results:**
- **Total Requests:** 3,010
- **Throughput (RPS):** ~30.2
- **Failures:** 0 (0%)
- **Latency (ms):**
  - Median: 23
  - p95: 62
  - p99: 102
  - Min: 17
  - Max: 118
  - Average: 27.8
- **Observation:** System handled sudden traffic surge without failures. p95 and p99 latencies increased as expected during scaling.

---

## 2. Bottlenecks Identified
1. **Model Loading on Cold Starts**  
   - Cloud Run scales to zero when idle; the first request after scaling can have added latency due to model load from GCS.
2. **Instance Spin-Up Latency**  
   - Sudden spikes trigger new instance creation, adding 1–2 seconds for scaling events.
3. **Single Threaded Processing**  
   - Current setup processes requests sequentially per worker; higher concurrency per instance could improve throughput.

---

## 3. Recommendations

### **Scaling Strategies**
- **Increase Minimum Instance Count**  
  Maintain at least 1–2 warm instances to reduce cold start impact for high-availability use cases.
- **Optimize Concurrency Settings**  
  Configure `--concurrency` in Cloud Run to allow each instance to handle multiple simultaneous requests.
- **Use Cloud Run CPU Always Allocated**  
  Keeps CPU available during idle to speed up model load.

### **Performance Optimizations**
- **Model Serialization**  
  Save the XGBoost model in binary format (`.bst`) instead of JSON for faster load times.
- **Batch Processing**  
  If applicable, allow the API to handle multiple prediction requests in a single call.
- **Lightweight Dependencies**  
  Continue using slim Python base images and remove unused dependencies to reduce container size and startup time.

---

## 4. Conclusion
Across all load profiles — baseline, normal, stress, and spike — the **Penguin API** demonstrated **high stability** with **0% failure rate** and **consistent sub-120 ms latencies**.  
Scaling behaviors were predictable, with slight latency increases during spikes due to Cloud Run instance spin-ups.  
Implementing the recommended scaling and optimization strategies can further minimize cold start delays and maintain low latency under extreme loads.

---
