# DevOps Lab 4 — Advanced Deployment Strategies & Enterprise DevOps

| Field | Details |
|---|---|
| **Name** | Arghyadipta Goswami |
| **Roll Number** | 2301010192 |
| **Section** | C |
| **Subject** | DEV OPS AUTOMATION |
| **Academic Year** | 2023–2027 |
| **Repository** | https://github.com/ArghyadiptaGoswami4259/DEV-OPS-LAB- |

---

## 1. Objective

To implement, test, and evaluate enterprise DevOps delivery practices covering automated CI/CD deployment gates, Blue-Green deployment, Canary traffic splitting and rollback, declarative GitOps reconciliation using Argo CD, secure secret management in Jenkins and Kubernetes, and persistent-storage disaster recovery and failover.

---

## 2. CI/CD Deployment Gates (Question 1)

A Flask service (`app.py`) and a six-test Pytest suite (`tests/test_unit.py` and `tests/test_integration.py`) are integrated into a declarative Jenkins pipeline (`Jenkinsfile`).

### Pipeline Design
1. **Secure Secret Management:** Loads the `lab4-api-key` credential via `withCredentials` with shell tracing disabled (`set +x`).
2. **Checkout:** Checks out the repository source via `checkout scm`.
3. **Install Dependencies:** Creates an isolated `.jenkins-venv` virtual environment and installs `requirements.txt`.
4. **Unit Tests:** Runs `pytest -v tests/test_unit.py` (3 arithmetic unit tests for `add(a, b)`).
5. **Integration Tests:** Runs `pytest -v tests/test_integration.py` (3 Flask test-client route tests checking `/`, `/health`, student identity metadata, and version `v1`).
6. **Deployment Gate:** Executes only when both test stages succeed; if any test stage fails, Jenkins skips downstream stages and invokes the `post { failure { ... } }` block (`Tests failed. Deployment BLOCKED.`).

### Verification Scope
- Local `pytest -v` verifies all 6 unit and integration tests pass against `app.py`.
- Demonstrating a failed CI gate requires temporarily introducing a failing assertion in `tests/test_unit.py`, pushing to GitHub, confirming Jenkins blocks the `Deployment Gate`, and then restoring the passing assertion.

---

## 3. Blue-Green Deployment (Question 2)

Two isolated instances of the containerized Flask application (`Dockerfile`) are defined in `bluegreen/compose.yaml`:
- **Blue (`blue`):** Runs with `APP_VERSION=v1` on internal port `5004`.
- **Green (`green`):** Runs with `APP_VERSION=v2` on internal port `5004`.
- **Nginx Reverse Proxy (`nginx`):** Exposed on `127.0.0.1:8086:80` and configured via `bluegreen/nginx.conf`.

### Switching & Operational Notes
- Initial traffic routes to `server blue:5004;` (`v1`).
- Promoting `green` (`v2`) updates the upstream in `bluegreen/nginx.conf` to `server green:5004;` and reloads Nginx.
- **Bind-Mount Inode Caveat:** When mounting a single file (`./nginx.conf:/etc/nginx/nginx.conf:ro`), utilities like `sed -i` create a new inode on the host, causing `nginx -s reload` inside the container to keep reading the old file until the proxy container is recreated (`docker compose -f bluegreen/compose.yaml up -d --force-recreate nginx`) or the file is modified in-place.
- **Advantages:** Near-instant traffic switch and rollback, pre-cutover validation of the Green environment via internal health checks (`/health`).
- **Limitations:** Requires duplicate compute capacity during cutover and careful backward/forward compatibility for shared state or database schemas.

---

## 4. Canary Deployment & Rollback (Question 3)

Progressive traffic shifting is configured in `canary/compose.yaml` and `canary/nginx.conf`, exposing the Nginx endpoint on `127.0.0.1:8087:80`.

### Traffic Progression Model
1. **Initial Canary Split (90% / 10%):** `canary/nginx.conf` assigns `weight=90` to `blue:5004` (`v1`) and `weight=10` to `green:5004` (`v2`).
2. **Expanded Canary Split (70% / 30%):** Adjusting weights to `weight=70` (Blue) and `weight=30` (Green) increases exposure to `v2` after verifying error rates and latency.
3. **Rollback (100% Blue):** Removing `green:5004` (or setting `blue` only) restores 100% of traffic to `v1`.

### Analysis
- **Advantages:** Limits blast radius to a controlled percentage of requests while validating real traffic behavior before full rollout.
- **Limitations:** Requires automated metrics sampling, clear rollback thresholds, and careful verification that Nginx has actually reloaded the updated weights on live traffic rather than relying solely on `nginx -t` exit codes.

---

## 5. GitOps Using Argo CD (Question 4)

Declarative Kubernetes manifests are maintained in `gitops/manifests/`:
- `gitops/manifests/deployment.yaml`: `gitops-demo` Deployment running `nginx:alpine` with `replicas: 3`.
- `gitops/manifests/service.yaml`: ClusterIP `Service` exposing port `80`.
- `gitops/argocd-application.yaml`: Argo CD `Application` pointing to `https://github.com/ArghyadiptaGoswami4259/DEV-OPS-LAB-.git` (`path: gitops/manifests`, `targetRevision: main`) with `automated.prune: true` and `automated.selfHeal: true`.

### Reconciliation Workflow
1. Argo CD deploys the initial manifest state from Git into the `default` namespace.
2. Updating `replicas` in Git (e.g., from `2` to `3`) causes Argo CD to detect the commit and sync the cluster to match Git.
3. With `selfHeal: true`, any out-of-band `kubectl scale` drift on the cluster is automatically reverted back to the Git-declared desired state.

---

## 6. Secure Secret Management (Question 5)

Secrets are kept completely out of source control using two complementary mechanisms:

### Jenkins Credentials
- A secret text credential (`lab4-api-key`) is stored in Jenkins' credential store.
- `Jenkinsfile` accesses it inside `withCredentials([string(credentialsId: 'lab4-api-key', variable: 'API_KEY')])` with `set +x` so neither command tracing nor echo output leaks the credential.

### Kubernetes Secrets
- The secret `lab4-app-secret` (key `API_KEY`) is created imperatively in the cluster (`kubectl create secret generic ...`) and never committed to Git.
- `secrets/secret-demo-pod.yaml` defines `lab4-secret-demo`, injecting `API_KEY` via `valueFrom.secretKeyRef` and validating presence without logging the secret plaintext.

### Security Best Practices
- Enforce least-privilege RBAC and credential scoping.
- Never commit `.env` files, API keys, or Secret manifests with plaintext values to Git.
- Rotate credentials regularly and integrate an external secret manager (e.g., HashiCorp Vault or cloud KMS/Secrets Manager) in production.

---

## 7. Disaster Recovery & Failover (Question 6)

Persistent storage recovery and manual proxy failover are structured in `disaster-recovery/` and `bluegreen/`:

### Storage Backup & Integrity Recovery
- `disaster-recovery/pvc.yaml` defines a `1Gi` `ReadWriteOnce` `PersistentVolumeClaim` (`lab4-dr-pvc`).
- `disaster-recovery/pod.yaml` mounts `lab4-dr-pvc` at `/data` inside `lab4-dr-pod`.
- Recovery drill workflow:
  1. Write sample data to `/data/records.txt` and record its SHA-256 digest.
  2. Back up the file locally under `disaster-recovery/backups/` (ignored by `.gitignore`).
  3. Simulate accidental deletion (`rm /data/records.txt`) and verify absence.
  4. Restore from backup (`kubectl cp`) while timing with sub-second precision (`date +%s.%N`) rather than coarse whole-second `date +%s` timestamps.
  5. Compare SHA-256 checksums between the backup and restored file to prove byte-level integrity.

### RTO and RPO Concepts
- **RTO (Recovery Time Objective):** Maximum tolerable downtime between failure detection and service restoration.
- **RPO (Recovery Point Objective):** Maximum tolerable data loss measured backward in time from the failure point (determined by backup/snapshot frequency).

### Service Failover Considerations
- Stopping `blue` while Nginx still routes to `server blue:5004;` causes HTTP `504 Gateway Time-out` / `502 Bad Gateway` errors.
- Recovering traffic onto `green` requires updating `bluegreen/nginx.conf` to `server green:5004;` and recreating/reloading the Nginx container so it no longer attempts DNS resolution for the stopped `blue` service. Without automated health probes and dynamic upstream switching, this represents manual recovery rather than zero-downtime automatic failover.

---

## 8. Deployment Strategy Comparison

| Strategy | Primary Benefit | Main Risk / Trade-off | Suitable Use Case |
|---|---|---|---|
| **Blue-Green** | Instant cutover and fast rollback between two identical environments | Duplicate infrastructure cost; stateful/DB schema compatibility | Major application releases requiring isolated pre-cutover validation |
| **Canary** | Gradual traffic exposure limits blast radius of defects | Requires traffic splitting, live telemetry, and clear rollback triggers | Risk-sensitive production updates and incremental validation |
| **GitOps (Argo CD)** | Declarative, Git-audited state with automated drift self-healing | Operational learning curve; requires strict Git access & secret hygiene | Continuous Kubernetes cluster delivery and multi-environment consistency |

---

## 9. Conclusion

This project consolidates automated CI/CD quality gates, progressive container delivery strategies (Blue-Green and Canary), declarative Kubernetes reconciliation (GitOps with Argo CD), non-exposed credential injection, and checksum-verified disaster recovery into a single reproducible repository for **DEV OPS AUTOMATION (2023–2027)**.
