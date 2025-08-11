## 📊 Test Coverage Report

**Command used**
pytest --cov=. --cov-report=term-missing tests/
Coverage output


Name                Stmts   Miss  Cover
---------------------------------------
app/main.py           151     41    73%
locustfile.py           0      0   100%
tests/test_api.py      70      6    91%
train.py               39     39     0%
---------------------------------------
TOTAL                 260     86    67%


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

