CI / CD for AI Orchestrator
==========================

This document explains how to rotate the Grok/xAI API key and how the GitHub Actions CI/CD pipelines are configured.

Rotate / Regenerate Grok (xAI) API key

- Visit your xAI / Grok account dashboard and create a new API key (or rotate the existing one) according to xAI's docs.
- Revoke the old key immediately after confirming the new key works.
- Never commit API keys into the repository. Use repository secrets instead.

Add secrets to GitHub repository

1. Go to your repository on GitHub → Settings → Secrets and variables → Actions → New repository secret.
2. Add the following secrets:
   - `XAI_API_KEY` — your Grok / xAI API key value.
   - `GITHUB_TOKEN` — (automatically provided by GitHub Actions) used to push to GHCR. If you need broader package permissions, create a PAT with `packages:write` and store it as `GHCR_PAT`, then update the workflow.
   - `DEPLOY_SSH_KEY` (optional) — private SSH key for deployment host.
   - `DEPLOY_USER` / `DEPLOY_HOST` (optional) — SSH user and host for deployment.
   Additional optional deploy targets and required secrets

   - AWS ECS:
      - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECS_CLUSTER`, `ECS_SERVICE`
   - GKE (Google Kubernetes Engine):
      - `GCP_SA_KEY` (JSON service account key), `GCP_PROJECT`, `GKE_CLUSTER`, `GKE_LOCATION`, `GKE_DEPLOYMENT`
   - AKS (Azure Kubernetes Service):
      - `AZURE_CREDENTIALS` (service principal JSON), `AKS_RESOURCE_GROUP`, `AKS_CLUSTER`, `AKS_DEPLOYMENT`
   - Generic Kubernetes / Helm deploy:
      - `KUBE_CONFIG_DATA` — base64-encoded kubeconfig for the target cluster. The CD workflow will restore this to `$HOME/.kube/config` and run `helm upgrade --install`.

   Set the corresponding secret(s) to enable each deploy job. The CD workflow checks for presence of these secrets and runs the matching job.

CI workflow (/.github/workflows/ci.yml)

- Runs on push and pull_request to `main` and `develop`.
- Installs Python 3.11, caches pip, installs dependencies (if `backend/requirements.txt` exists), runs `pytest` under `backend`.
- Passes `XAI_API_KEY` and `LLM_TEST_MODE` via environment variables to the job (read from repository secrets).

CD workflow (/.github/workflows/cd.yml)

- Runs on push to `main`.
- Builds a Docker image using `backend/Dockerfile` and pushes image tags to GitHub Container Registry (GHCR).
- Optional `deploy` job can SSH to a host and run the new image. Configure `DEPLOY_SSH_KEY`, `DEPLOY_USER`, and `DEPLOY_HOST` secrets to enable this step.

Notes and recommendations

- After rotating the API key, update GitHub secret `XAI_API_KEY` with the new value.
- If you previously pushed secrets, you've already completed a history purge — do not reintroduce secrets.
- For production deployments consider using a proper secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) and a CI environment with least-privilege secrets.
