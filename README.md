# DevOps Lab 4 — Advanced Deployment Strategies

> **Student Details**
> - **Name:** Arghyadipta Goswami
> - **Roll Number:** 2301010192
> - **Section:** C
> - **Subject:** DEV OPS AUTOMATION
> - **Year:** 2023–2027
> - **Repository:** https://github.com/ArghyadiptaGoswami4259/DEV-OPS-LAB-

This project implements enterprise DevOps workflows covering automated CI/CD deployment gates, Blue-Green deployment, Canary rollouts and rollbacks, GitOps reconciliation with Argo CD, secure secret management, and disaster recovery.

## Technologies

- Python, Flask, Pytest
- Jenkins CI/CD (`Jenkinsfile`)
- Docker & Docker Compose
- Nginx reverse proxy & weighted load balancing
- Kubernetes (Minikube)
- Argo CD (GitOps)

## Lab Questions

| Question | Topic | Implementation Path |
|---|---|---|
| Q1 | Automated testing and deployment gates | `app.py`, `tests/`, `Jenkinsfile` |
| Q2 | Blue-Green deployment | `Dockerfile`, `bluegreen/` |
| Q3 | Canary deployment and rollback | `canary/` |
| Q4 | GitOps using Argo CD | `gitops/` |
| Q5 | Secure secret management | `Jenkinsfile`, `secrets/` |
| Q6 | Disaster recovery and failover | `disaster-recovery/` |
| Q7 | Advanced deployment strategies report | [`REPORT.md`](REPORT.md) |

## Project Structure

```text
.
├── .gitignore
├── Dockerfile
├── Jenkinsfile
├── README.md
├── REPORT.md
├── app.py
├── requirements.txt
├── bluegreen/
│   ├── compose.yaml
│   └── nginx.conf
├── canary/
│   ├── compose.yaml
│   └── nginx.conf
├── disaster-recovery/
│   ├── pod.yaml
│   └── pvc.yaml
├── docs/
│   └── EXECUTION-GUIDE.md
├── gitops/
│   ├── argocd-application.yaml
│   └── manifests/
│       ├── deployment.yaml
│       └── service.yaml
├── secrets/
│   └── secret-demo-pod.yaml
└── tests/
    ├── test_integration.py
    └── test_unit.py
```

## Run Tests Locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -v
```

The test suite contains 3 unit tests (`tests/test_unit.py`) and 3 integration tests (`tests/test_integration.py`) that are executed as gated stages in the `Jenkinsfile`.

## Blue-Green Deployment

Start the Blue (`v1`), Green (`v2`), and Nginx containers:

```bash
docker compose -f bluegreen/compose.yaml up -d --build
curl http://localhost:8086/
```

To switch traffic from Blue (`v1`) to Green (`v2`), update `bluegreen/nginx.conf` to point to `green:5004` and recreate or reload Nginx (see [`docs/EXECUTION-GUIDE.md`](docs/EXECUTION-GUIDE.md) for bind-mount safe reload commands).

## Canary Deployment

Start the Canary stack (configured initially with a 90% Blue / 10% Green split):

```bash
docker compose -f canary/compose.yaml up -d --build
curl http://localhost:8087/
```

Progressive weights (`70/30`) and rollback (`100%` Blue) are controlled via `canary/nginx.conf`.

## GitOps (Argo CD)

Kubernetes manifests live under `gitops/manifests/`, and the Argo CD `Application` definition in `gitops/argocd-application.yaml` points to:

```text
https://github.com/ArghyadiptaGoswami4259/DEV-OPS-LAB-.git (path: gitops/manifests)
```

Automated sync (`prune: true`, `selfHeal: true`) keeps the cluster synchronized with Git.

## Secret Management

- **Jenkins:** Uses `withCredentials` (`lab4-api-key`) with `set +x` and secret masking so values are never printed in console logs.
- **Kubernetes:** Uses `secrets/secret-demo-pod.yaml` with `secretKeyRef` referencing `lab4-app-secret` (created out-of-band via `kubectl create secret`, never committed to Git).

## Disaster Recovery

`disaster-recovery/pvc.yaml` and `disaster-recovery/pod.yaml` provision a `PersistentVolumeClaim` (`lab4-dr-pvc`) mounted at `/data` inside `lab4-dr-pod` for backup, deletion simulation, restore, and SHA-256 checksum verification.

## Documentation & Execution Guide

- Complete lab report: [`REPORT.md`](REPORT.md)
- Step-by-step runbook for all lab tasks: [`docs/EXECUTION-GUIDE.md`](docs/EXECUTION-GUIDE.md)
