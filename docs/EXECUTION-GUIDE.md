# Execution Guide — DevOps Lab 4

**Student:** Arghyadipta Goswami | **Roll:** 2301010192 | **Section:** C  
**Subject:** DEV OPS AUTOMATION | **Year:** 2023–2027  
**Repository:** https://github.com/ArghyadiptaGoswami4259/DEV-OPS-LAB-

Use this runbook to execute each lab question in your local environment (Ubuntu/WSL2, Docker, Jenkins, Minikube, Argo CD) and capture authentic verification outputs.

---

## Q1: Automated Testing & CI/CD Pipeline Gates

1. **Run tests locally:**
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python -m pytest -v
   ```
2. **Configure Jenkins job:**
   - Create a Pipeline job in Jenkins pointing to `https://github.com/ArghyadiptaGoswami4259/DEV-OPS-LAB-.git` (branch `main`, script path `Jenkinsfile`).
   - First register the credential required for Q5 (`lab4-api-key`) or run build #1 after registering it.
3. **Verify pass → fail → pass gate behavior:**
   - Run Build #1 with passing tests → confirm `Deployment Gate` prints `All tests passed. Deployment approved...`.
   - Temporarily break an assertion in `tests/test_unit.py`, commit & push → trigger Build #2 → confirm `Integration Tests` and `Deployment Gate` are skipped and pipeline ends with `FAILURE`.
   - Restore the assertion in `tests/test_unit.py`, commit & push → trigger Build #3 → confirm `SUCCESS`.

---

## Q2: Blue-Green Deployment

1. **Start Blue (`v1`), Green (`v2`), and Nginx:**
   ```bash
   docker compose -f bluegreen/compose.yaml up -d --build
   docker compose -f bluegreen/compose.yaml ps
   curl -s http://localhost:8086/
   ```
2. **Verify Green health directly:**
   ```bash
   docker compose -f bluegreen/compose.yaml exec -T green \
     python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5004/health').read().decode())"
   ```
3. **Switch traffic from Blue to Green cleanly:**
   > **Important:** Because `bluegreen/compose.yaml` bind-mounts `./nginx.conf` as a single file, `sed -i` replaces the host inode and leaves the running container pointing at the old file until Nginx is recreated. Always recreate the `nginx` service or overwrite the file in-place.
   ```bash
   python3 -c '
   p = "bluegreen/nginx.conf"
   with open(p, "r") as f: s = f.read()
   with open(p, "w") as f: f.write(s.replace("server blue:5004;", "server green:5004;"))
   '
   docker compose -f bluegreen/compose.yaml exec -T nginx nginx -t
   docker compose -f bluegreen/compose.yaml up -d --force-recreate nginx
   curl -i http://localhost:8086/
   ```
   Verify the returned JSON shows `"version": "v2"`.
4. **Rollback back to Blue (`v1`):**
   Replace `server green:5004;` back with `server blue:5004;`, recreate `nginx`, and verify `curl -s http://localhost:8086/` returns `"version": "v1"`.

---

## Q3: Canary Deployment & Rollback

1. **Start Canary stack (90% Blue / 10% Green):**
   ```bash
   docker compose -f canary/compose.yaml up -d --build
   ```
2. **Sample 100 requests for the 90/10 split:**
   ```bash
   python3 - <<'PY'
   import json, urllib.request
   from collections import Counter
   results = Counter()
   for _ in range(100):
       with urllib.request.urlopen("http://localhost:8087/") as r:
           results[json.load(r)["version"]] += 1
   print("Canary 90/10 results:", dict(results))
   PY
   ```
3. **Increase Canary weight to 70/30:**
   Update `weight=90` → `weight=70` and `weight=10` → `weight=30` in `canary/nginx.conf`, run `docker compose -f canary/compose.yaml up -d --force-recreate nginx`, and re-run the 100-request Python sampler to confirm ~70 `v1` / ~30 `v2`.
4. **Demonstrate rollback to 100% Blue (`v1`):**
   Keep only `server blue:5004;` in `canary/nginx.conf`, recreate `nginx`, and run the 100-request sampler to confirm `{'v1': 100}`.

---

## Q4: GitOps Using Argo CD

1. **Start Minikube & install Argo CD:**
   ```bash
   minikube start
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   kubectl get pods -n argocd
   ```
2. **Apply the declarative Argo CD Application:**
   ```bash
   kubectl apply -f gitops/argocd-application.yaml
   kubectl get applications -n argocd
   ```
3. **Verify deployment & self-healing:**
   ```bash
   kubectl get deployments,pods,svc -l app=gitops-demo
   # Simulate manual drift (Argo CD selfHeal will revert back to replicas=3):
   kubectl scale deployment gitops-demo --replicas=1
   kubectl get deployment gitops-demo -w
   ```

---

## Q5: Secure Secret Management

1. **Jenkins Credential:**
   - In Jenkins UI: **Manage Jenkins → Credentials → System → Global credentials → Add Credentials**
   - Kind: **Secret text**, ID: `lab4-api-key`, Secret: `<your-test-secret-value>`
   - Run the Jenkins pipeline and confirm `Secure Secret Management` masks `$API_KEY` and prints `Secret validation successful`.
2. **Kubernetes Secret:**
   ```bash
   kubectl create secret generic lab4-app-secret --from-literal=API_KEY='demo-secret-value-do-not-commit'
   kubectl apply -f secrets/secret-demo-pod.yaml
   kubectl wait --for=condition=Ready pod/lab4-secret-demo --timeout=120s
   kubectl logs lab4-secret-demo
   ```

---

## Q6: Disaster Recovery & Failover

1. **Provision PVC and Pod:**
   ```bash
   kubectl apply -f disaster-recovery/pvc.yaml
   kubectl apply -f disaster-recovery/pod.yaml
   kubectl wait --for=condition=Ready pod/lab4-dr-pod --timeout=120s
   ```
2. **Create data, backup, delete, restore, and verify checksums:**
   ```bash
   mkdir -p disaster-recovery/backups
   kubectl exec lab4-dr-pod -- sh -c 'echo "Arghyadipta Goswami (2301010192) - DR test record" > /data/records.txt'
   kubectl cp lab4-dr-pod:/data/records.txt disaster-recovery/backups/records.txt
   sha256sum disaster-recovery/backups/records.txt

   START=$(date +%s.%N)
   kubectl exec lab4-dr-pod -- rm /data/records.txt
   kubectl exec lab4-dr-pod -- ls /data/records.txt || true
   kubectl cp disaster-recovery/backups/records.txt lab4-dr-pod:/data/records.txt
   END=$(date +%s.%N)

   kubectl exec lab4-dr-pod -- cat /data/records.txt
   kubectl exec lab4-dr-pod -- sha256sum /data/records.txt
   python3 -c "print(f'Elapsed recovery duration: {float($END) - float($START):.3f} seconds')"
   ```
3. **Manual Failover Test (Blue-Green):**
   - Stop `blue`: `docker compose -f bluegreen/compose.yaml stop blue`
   - Observe failure on `curl -i --max-time 5 http://localhost:8086/` (HTTP 504).
   - Switch `bluegreen/nginx.conf` to `server green:5004;` and run `docker compose -f bluegreen/compose.yaml up -d --force-recreate nginx`.
   - Confirm `curl -i http://localhost:8086/` recovers with `HTTP/1.1 200 OK` and `"version": "v2"`.
