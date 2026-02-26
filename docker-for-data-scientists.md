# Docker: Complete Guide for Senior Data Scientists

> From fundamentals to production-grade workflows — everything you need to know.

---

## Table of Contents

1. [What is Docker?](#1-what-is-docker)
2. [Why Docker? The Problem It Solves](#2-why-docker-the-problem-it-solves)
3. [Core Concepts](#3-core-concepts)
4. [Installation & Setup](#4-installation--setup)
5. [Essential Commands](#5-essential-commands)
6. [Dockerfile Deep Dive](#6-dockerfile-deep-dive)
7. [Docker Compose](#7-docker-compose)
8. [Data Science Use Cases](#8-data-science-use-cases)
9. [Docker for ML Pipelines](#9-docker-for-ml-pipelines)
10. [Docker for Model Serving](#10-docker-for-model-serving)
11. [Volumes & Data Persistence](#11-volumes--data-persistence)
12. [Networking](#12-networking)
13. [Docker Registry & Image Management](#13-docker-registry--image-management)
14. [Performance & Optimization](#14-performance--optimization)
15. [Security Best Practices](#15-security-best-practices)
16. [Advanced Patterns](#16-advanced-patterns)
17. [Docker in CI/CD](#17-docker-in-cicd)
18. [GPU Support for Deep Learning](#18-gpu-support-for-deep-learning)
19. [Kubernetes Transition](#19-kubernetes-transition)
20. [Common Pitfalls](#20-common-pitfalls)
21. [Quick Reference Cheatsheet](#21-quick-reference-cheatsheet)

---

## 1. What is Docker?

Docker is an **open-source containerization platform** that packages your application and all its dependencies into a standardized unit called a **container**.

Think of it as a lightweight, portable virtual machine — but instead of virtualizing hardware, Docker virtualizes the operating system at the process level.

```
Traditional VM                   Docker Container
┌────────────────────┐           ┌────────────────────┐
│    Application     │           │    Application     │
│    Libraries       │           │    Libraries       │
│    Guest OS        │           │    (no Guest OS)   │
│    Hypervisor      │           │    Docker Engine   │
│    Host OS         │           │    Host OS         │
│    Hardware        │           │    Hardware        │
└────────────────────┘           └────────────────────┘
   ~GBs, minutes to boot            ~MBs, seconds to start
```

### Key Components

| Component       | Description |
|-----------------|-------------|
| **Docker Engine**  | Runtime that builds and runs containers |
| **Docker Image**   | Read-only blueprint/template for a container |
| **Docker Container** | Running instance of an image |
| **Dockerfile**    | Text file with instructions to build an image |
| **Docker Hub**    | Public registry to store/share images |
| **Docker Compose** | Tool for multi-container applications |

---

## 2. Why Docker? The Problem It Solves

### The Classic Problem: "It works on my machine"

```
Data Scientist's Laptop          Production Server
Python 3.11                      Python 3.8
scikit-learn 1.3                 scikit-learn 0.24
pandas 2.0                       pandas 1.3
CUDA 11.8                        CUDA 10.2
Ubuntu 22.04                     CentOS 7
```

Result: Model fails in production, debugging takes days.

### With Docker

```
Docker Image (built once)
├── Python 3.11
├── scikit-learn 1.3
├── pandas 2.0
├── CUDA 11.8
└── your code

Runs identically everywhere:
  ✓ Laptop
  ✓ Colleague's machine
  ✓ CI/CD pipeline
  ✓ Cloud VM
  ✓ Kubernetes cluster
```

### Why Data Scientists Specifically Need Docker

1. **Reproducibility** — Experiments produce identical results across environments
2. **Dependency isolation** — Project A uses TF 1.x, Project B uses TF 2.x — no conflicts
3. **Collaboration** — Share entire environments, not just `requirements.txt`
4. **Production deployment** — Same container used in development ships to production
5. **Scalability** — Easy horizontal scaling of model inference services
6. **MLOps** — Standard unit of deployment in modern ML platforms (SageMaker, Vertex AI, MLflow)

---

## 3. Core Concepts

### Image vs Container

```
Image = Recipe (static, read-only)
Container = Cake baked from the recipe (running process)

You can bake many cakes from one recipe.
You can run many containers from one image.
```

### Layers

Docker images are built in **layers**. Each instruction in a Dockerfile creates a new layer.

```
Layer 5: COPY model.pkl /app/          ← your code
Layer 4: RUN pip install -r requirements.txt
Layer 3: COPY requirements.txt /app/
Layer 2: RUN apt-get install -y libgomp1
Layer 1: FROM python:3.11-slim         ← base image
```

Layers are **cached** — if Layer 3 doesn't change, Docker reuses cached Layers 1-3 and only rebuilds 4-5. This is critical for fast builds.

### Image Naming Convention

```
[registry]/[username]/[repository]:[tag]

Examples:
  python:3.11-slim                   # official Docker Hub image
  mycompany/ml-base:v1.2             # private registry
  gcr.io/myproject/inference:latest  # Google Container Registry
```

---

## 4. Installation & Setup

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER        # run docker without sudo
newgrp docker                        # apply group change

# macOS
# Install Docker Desktop from https://docker.com

# Verify installation
docker --version                     # Docker version 24.x.x
docker run hello-world               # test run
```

### Docker Desktop vs Docker Engine

- **Docker Desktop** (Mac/Windows): GUI + engine, includes Docker Compose
- **Docker Engine** (Linux): CLI only, production servers

---

## 5. Essential Commands

### Working with Images

```bash
# Pull an image from Docker Hub
docker pull python:3.11-slim

# List local images
docker images

# Remove an image
docker rmi python:3.11-slim

# Search Docker Hub
docker search jupyter

# Inspect image metadata
docker inspect python:3.11-slim

# View image layers/history
docker history python:3.11-slim
```

### Working with Containers

```bash
# Run a container (interactive)
docker run -it python:3.11-slim bash

# Run a container (detached/background)
docker run -d --name my-jupyter -p 8888:8888 jupyter/scipy-notebook

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop a container
docker stop my-jupyter

# Start a stopped container
docker start my-jupyter

# Remove a container
docker rm my-jupyter

# View container logs
docker logs my-jupyter
docker logs -f my-jupyter              # follow/stream logs

# Execute a command inside running container
docker exec -it my-jupyter bash
docker exec my-jupyter python -c "import pandas; print(pandas.__version__)"

# Copy files between host and container
docker cp my-jupyter:/home/jovyan/work/notebook.ipynb ./
docker cp ./data.csv my-jupyter:/home/jovyan/work/

# Resource stats
docker stats my-jupyter
```

### Run Flags You Must Know

```bash
docker run \
  -it \                        # interactive + TTY (for shell access)
  -d \                         # detached (background)
  --name my-container \        # give it a name
  -p 8888:8888 \               # port mapping: host:container
  -p 5000:5000 \               # multiple ports
  -v /host/path:/container/path \  # volume mount
  -e MY_VAR=value \            # environment variable
  -e API_KEY=$API_KEY \        # from host env
  --env-file .env \            # from env file
  --memory 4g \                # memory limit
  --cpus 2 \                   # CPU limit
  --rm \                       # remove container when it stops
  --gpus all \                 # GPU access (nvidia-docker)
  --network my-network \       # attach to network
  --restart unless-stopped \   # auto-restart policy
  my-image:tag
```

---

## 6. Dockerfile Deep Dive

A Dockerfile is a script of instructions to build your image.

### Basic Structure

```dockerfile
# Base image
FROM python:3.11-slim

# Metadata
LABEL maintainer="data-scientist@company.com"
LABEL version="1.0"

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*   # clean up to reduce layer size

# Copy dependency file FIRST (for cache efficiency)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code (changes most often → last)
COPY . .

# Create non-root user (security)
RUN useradd --create-home appuser
USER appuser

# What to run when container starts
CMD ["python", "app.py"]
```

### Dockerfile Instructions Reference

| Instruction | Purpose | Example |
|-------------|---------|---------|
| `FROM` | Base image | `FROM python:3.11-slim` |
| `RUN` | Execute command (build time) | `RUN pip install pandas` |
| `COPY` | Copy files from host to image | `COPY . /app` |
| `ADD` | Like COPY but supports URLs/tar | `ADD data.tar.gz /data/` |
| `WORKDIR` | Set working directory | `WORKDIR /app` |
| `ENV` | Set environment variables | `ENV DEBUG=0` |
| `ARG` | Build-time variables | `ARG VERSION=latest` |
| `EXPOSE` | Document ports (informational) | `EXPOSE 8080` |
| `CMD` | Default command (overridable) | `CMD ["python", "serve.py"]` |
| `ENTRYPOINT` | Fixed command (CMD appends to it) | `ENTRYPOINT ["python"]` |
| `VOLUME` | Declare mount points | `VOLUME /data` |
| `USER` | Set user context | `USER appuser` |
| `HEALTHCHECK` | Container health check | `HEALTHCHECK CMD curl -f http://localhost/health` |

### CMD vs ENTRYPOINT

```dockerfile
# CMD only — entire command is replaceable
CMD ["python", "train.py"]
# docker run myimage python eval.py  → runs eval.py instead

# ENTRYPOINT + CMD — entrypoint is fixed, CMD provides defaults
ENTRYPOINT ["python"]
CMD ["train.py"]
# docker run myimage eval.py  → runs: python eval.py
```

### Multi-Stage Builds (Advanced)

Dramatically reduce image size by separating build and runtime stages.

```dockerfile
# Stage 1: Builder (large, has all build tools)
FROM python:3.11 AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y gcc g++ build-essential
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime (lean, production image)
FROM python:3.11-slim AS runtime
WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY src/ .

ENV PATH=/root/.local/bin:$PATH
USER nobody

CMD ["python", "serve.py"]

# Result: Builder ~1.5GB → Runtime ~200MB
```

### .dockerignore

Like `.gitignore` — prevents unnecessary files from being sent to Docker build context.

```dockerignore
# .dockerignore
__pycache__/
*.pyc
*.pyo
.git/
.gitignore
.env
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
notebooks/               # exclude raw notebooks from prod image
data/raw/                # exclude large data files
models/                  # exclude trained models (mount as volume)
*.ipynb_checkpoints/
```

---

## 7. Docker Compose

Docker Compose manages **multi-container applications** using a single YAML file.

### Why Compose?

A data science stack might need:
- Jupyter notebook server
- PostgreSQL database
- Redis cache
- MLflow tracking server
- MinIO object storage

Managing these with individual `docker run` commands is messy. Compose ties them together.

### Basic docker-compose.yml

```yaml
version: "3.9"

services:
  # Jupyter Notebook
  notebook:
    image: jupyter/scipy-notebook:latest
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/home/jovyan/work
      - ./data:/home/jovyan/data
    environment:
      - JUPYTER_ENABLE_LAB=yes
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - mlflow
      - postgres

  # MLflow Tracking Server
  mlflow:
    image: python:3.11-slim
    command: >
      bash -c "pip install mlflow boto3 psycopg2-binary &&
               mlflow server
               --host 0.0.0.0
               --port 5000
               --backend-store-uri postgresql://mlflow:secret@postgres/mlflow
               --default-artifact-root s3://mlflow-artifacts"
    ports:
      - "5000:5000"
    environment:
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin
      - MLFLOW_S3_ENDPOINT_URL=http://minio:9000
    depends_on:
      - postgres
      - minio

  # PostgreSQL Database
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=mlflow
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=mlflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # MinIO (S3-compatible storage)
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data

  # Model Inference API
  inference-api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./models:/models:ro        # read-only model mount
    environment:
      - MODEL_PATH=/models/best_model.pkl
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  postgres_data:
  minio_data:
```

### Compose Commands

```bash
# Start all services (background)
docker compose up -d

# Start and rebuild images
docker compose up -d --build

# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f mlflow

# Scale a service
docker compose up -d --scale inference-api=3

# Stop all services
docker compose down

# Stop and remove volumes (CAUTION: deletes data)
docker compose down -v

# Run one-off command in a service
docker compose run --rm notebook python train.py

# Execute in running container
docker compose exec notebook bash

# View service status
docker compose ps
```

---

## 8. Data Science Use Cases

### Use Case 1: Reproducible Research Environment

**Problem**: You published a paper. Reviewers can't reproduce results 6 months later.

```dockerfile
# Dockerfile.research
FROM python:3.11.4-slim

WORKDIR /research

# Pin exact versions for reproducibility
RUN pip install \
    numpy==1.24.3 \
    pandas==2.0.2 \
    scikit-learn==1.3.0 \
    scipy==1.11.1 \
    matplotlib==3.7.2 \
    seaborn==0.12.2 \
    jupyter==1.0.0

COPY . .

# Set random seeds via environment
ENV RANDOM_SEED=42 \
    PYTHONHASHSEED=42

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--no-browser", "--allow-root"]
```

```bash
# Anyone can reproduce your exact environment
docker build -t my-paper-env:v1 -f Dockerfile.research .
docker run -p 8888:8888 -v $(pwd)/notebooks:/research/notebooks my-paper-env:v1
```

### Use Case 2: Isolated Python Environments (Better than virtualenv)

```bash
# Need to test your code with different Python versions?
docker run --rm -v $(pwd):/app -w /app python:3.9 python test.py
docker run --rm -v $(pwd):/app -w /app python:3.10 python test.py
docker run --rm -v $(pwd):/app -w /app python:3.11 python test.py
```

### Use Case 3: Database for Local Development

```bash
# Spin up PostgreSQL without installing it
docker run -d \
  --name local-postgres \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=mydata \
  -p 5432:5432 \
  postgres:15

# Connect with psycopg2
# postgresql://postgres:secret@localhost:5432/mydata
```

### Use Case 4: Running Spark Locally

```yaml
# docker-compose-spark.yml
version: "3.9"
services:
  spark-master:
    image: bitnami/spark:3.4
    environment:
      - SPARK_MODE=master
    ports:
      - "8080:8080"   # Spark UI
      - "7077:7077"   # Spark master port

  spark-worker:
    image: bitnami/spark:3.4
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2G
    depends_on:
      - spark-master

  notebook:
    image: jupyter/pyspark-notebook
    ports:
      - "8888:8888"
    environment:
      - SPARK_MASTER=spark://spark-master:7077
```

```bash
docker compose -f docker-compose-spark.yml up -d
```

---

## 9. Docker for ML Pipelines

### Containerized Training Job

```dockerfile
# Dockerfile.train
FROM python:3.11-slim

WORKDIR /train

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements-train.txt .
RUN pip install -r requirements-train.txt

COPY src/train.py .
COPY src/utils.py .

ENTRYPOINT ["python", "train.py"]
# Allows: docker run train-image --epochs 50 --lr 0.001
```

```python
# train.py
import argparse
import mlflow

parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=int, default=10)
parser.add_argument("--lr", type=float, default=0.01)
parser.add_argument("--data-path", default="/data/train.csv")
args = parser.parse_args()

with mlflow.start_run():
    mlflow.log_params(vars(args))
    # ... training code ...
    mlflow.log_metric("accuracy", accuracy)
    mlflow.sklearn.log_model(model, "model")
```

```bash
# Run training with different hyperparameters
docker run \
  -v $(pwd)/data:/data \
  -v $(pwd)/mlruns:/mlruns \
  -e MLFLOW_TRACKING_URI=http://mlflow-server:5000 \
  train-image:v1 \
  --epochs 100 --lr 0.001
```

### Parameterized Experiment Runner

```bash
#!/bin/bash
# run_experiments.sh — grid search via Docker

for lr in 0.001 0.01 0.1; do
  for batch_size in 32 64 128; do
    docker run -d \
      --name "exp_lr${lr}_bs${batch_size}" \
      -v $(pwd)/data:/data \
      train-image:v1 \
      --lr $lr --batch-size $batch_size
  done
done

# Monitor all running experiments
docker stats $(docker ps --format "{{.Names}}" | grep "^exp_")
```

### Feature Engineering Pipeline

```dockerfile
# Dockerfile.features
FROM python:3.11-slim

WORKDIR /pipeline

COPY requirements-pipeline.txt .
RUN pip install -r requirements-pipeline.txt

COPY src/feature_engineering.py .

ENTRYPOINT ["python", "feature_engineering.py"]
```

```yaml
# docker-compose-pipeline.yml
version: "3.9"

services:
  ingest:
    build:
      context: .
      dockerfile: Dockerfile.ingest
    volumes:
      - raw_data:/data/raw
    command: ["--source", "s3://bucket/data.csv"]

  features:
    build:
      context: .
      dockerfile: Dockerfile.features
    volumes:
      - raw_data:/data/raw:ro
      - processed_data:/data/processed
    depends_on:
      ingest:
        condition: service_completed_successfully

  train:
    build:
      context: .
      dockerfile: Dockerfile.train
    volumes:
      - processed_data:/data/processed:ro
      - models:/models
    depends_on:
      features:
        condition: service_completed_successfully
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000

volumes:
  raw_data:
  processed_data:
  models:
```

---

## 10. Docker for Model Serving

### FastAPI Model Server

```python
# api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import numpy as np
import os

app = FastAPI(title="ML Model API")

# Load model at startup
model_path = os.environ.get("MODEL_PATH", "/models/model.pkl")
with open(model_path, "rb") as f:
    model = pickle.load(f)

class PredictRequest(BaseModel):
    features: list[float]

class PredictResponse(BaseModel):
    prediction: float
    confidence: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    try:
        X = np.array(request.features).reshape(1, -1)
        pred = model.predict(X)[0]
        proba = model.predict_proba(X).max()
        return PredictResponse(prediction=float(pred), confidence=float(proba))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```dockerfile
# api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install fastapi uvicorn scikit-learn numpy

COPY main.py .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```bash
# Build and run
docker build -t ml-api:v1 ./api
docker run -d \
  --name ml-api \
  -p 8000:8000 \
  -v $(pwd)/models:/models:ro \
  -e MODEL_PATH=/models/model.pkl \
  ml-api:v1

# Test
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [1.2, 3.4, 5.6, 7.8]}'
```

### Gradio Demo App

```dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN pip install gradio scikit-learn pandas

COPY app.py .
COPY models/ ./models/

EXPOSE 7860
CMD ["python", "app.py"]
```

```bash
docker run -p 7860:7860 my-gradio-demo
# Access at http://localhost:7860
```

---

## 11. Volumes & Data Persistence

Containers are **ephemeral** — data is lost when a container is removed. Volumes solve this.

### Types of Storage

```
1. Bind Mounts: /host/path → /container/path (host-managed)
2. Named Volumes: docker managed storage (docker volume create)
3. tmpfs Mounts: in-memory only (not persisted)
```

### Bind Mounts — for Development

```bash
# Mount current directory into container
docker run -v $(pwd)/data:/app/data my-image

# Read-only mount (protect your data)
docker run -v $(pwd)/models:/models:ro my-image
```

### Named Volumes — for Production Data

```bash
# Create a named volume
docker volume create ml-data

# Use named volume
docker run -v ml-data:/data my-image

# List volumes
docker volume ls

# Inspect volume (shows where data lives on host)
docker volume inspect ml-data

# Remove volume
docker volume rm ml-data

# Backup a volume
docker run --rm \
  -v ml-data:/data:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/ml-data-backup.tar.gz /data
```

### Volume Best Practices for Data Scientists

```yaml
services:
  notebook:
    volumes:
      # Source code: bind mount for live editing
      - ./notebooks:/home/jovyan/work

      # Large datasets: named volume (not checked into git)
      - datasets:/home/jovyan/data

      # Trained models: named volume with backup strategy
      - trained-models:/home/jovyan/models

      # Temporary scratch space: tmpfs (fast, not persisted)
      - type: tmpfs
        target: /tmp/scratch

volumes:
  datasets:
  trained-models:
```

---

## 12. Networking

### Default Networks

```bash
# Containers on the same compose network can talk by service name
# In docker-compose.yml:
#   mlflow service can reach postgres at hostname "postgres"
#   notebook can reach mlflow at hostname "mlflow"

# List networks
docker network ls

# Inspect a network
docker network inspect my-project_default
```

### Custom Networks

```yaml
# docker-compose.yml
networks:
  frontend:       # notebook ↔ api communication
  backend:        # api ↔ database communication (isolated from notebook)

services:
  notebook:
    networks:
      - frontend

  api:
    networks:
      - frontend
      - backend

  postgres:
    networks:
      - backend     # notebook cannot directly access postgres!
```

### Port Mapping

```bash
# -p HOST_PORT:CONTAINER_PORT
docker run -p 8888:8888 jupyter/scipy-notebook   # same ports
docker run -p 9999:8888 jupyter/scipy-notebook   # different host port
docker run -p 127.0.0.1:8888:8888 jupyter/scipy-notebook  # localhost only (secure)
```

---

## 13. Docker Registry & Image Management

### Docker Hub

```bash
# Login
docker login

# Tag image for pushing
docker tag my-model-api:v1 myusername/my-model-api:v1

# Push
docker push myusername/my-model-api:v1

# Pull
docker pull myusername/my-model-api:v1
```

### Private Registry (AWS ECR example)

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag ml-api:v1 123456789.dkr.ecr.us-east-1.amazonaws.com/ml-api:v1
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/ml-api:v1
```

### Image Tagging Strategy

```bash
# Tag with version + git SHA + environment
docker build -t ml-api:1.2.3 .
docker tag ml-api:1.2.3 ml-api:$(git rev-parse --short HEAD)
docker tag ml-api:1.2.3 ml-api:latest   # only for stable releases!
docker tag ml-api:1.2.3 ml-api:prod
```

---

## 14. Performance & Optimization

### Reducing Image Size

```dockerfile
# BAD: uses full python image
FROM python:3.11                          # ~1GB

# GOOD: use slim
FROM python:3.11-slim                     # ~150MB

# BETTER: use Alpine (smallest, but can cause issues with some packages)
FROM python:3.11-alpine                   # ~60MB

# BEST for data science: use specific slim + multi-stage
FROM python:3.11-slim AS base
```

### Optimize Layer Caching

```dockerfile
# BAD: invalidates cache on any code change
COPY . .
RUN pip install -r requirements.txt

# GOOD: requirements change less often than code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .                                  # only this layer rebuilds on code change
```

### Combine RUN Commands

```dockerfile
# BAD: each RUN is a separate layer
RUN apt-get update
RUN apt-get install -y libgomp1
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# GOOD: one layer, smaller image
RUN apt-get update && \
    apt-get install -y libgomp1 curl && \
    rm -rf /var/lib/apt/lists/*
```

### Use BuildKit (Modern Build System)

```bash
# Enable BuildKit for faster builds, better caching
export DOCKER_BUILDKIT=1

# Or set in daemon.json:
# { "features": { "buildkit": true } }

# BuildKit cache mount (speeds up pip install significantly)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Dockerfile with BuildKit Cache

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Cache pip downloads across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .
CMD ["python", "app.py"]
```

---

## 15. Security Best Practices

### Don't Run as Root

```dockerfile
# Create a non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --create-home appuser

# Switch to non-root user
USER appuser

# All subsequent commands run as appuser
CMD ["python", "serve.py"]
```

### Never Bake Secrets into Images

```dockerfile
# BAD — secret visible in image history!
ENV AWS_SECRET_KEY=mysecretkey123
RUN aws s3 cp s3://bucket/model.pkl .

# GOOD — pass secrets at runtime
# docker run -e AWS_SECRET_KEY=$AWS_SECRET_KEY my-image
```

### Use Docker Secrets (for Compose/Swarm)

```yaml
# docker-compose.yml
services:
  api:
    image: ml-api:v1
    secrets:
      - db_password
      - api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true    # managed by Docker Swarm
```

### Scan Images for Vulnerabilities

```bash
# Docker Scout (built into Docker Desktop)
docker scout cves my-image:v1

# Or use Trivy (open source)
trivy image my-image:v1
```

### Minimize Attack Surface

```dockerfile
# Use specific base image version (not :latest)
FROM python:3.11.4-slim-bookworm       # pinned version

# Only install what you need
RUN pip install --no-deps -r requirements.txt

# Remove build tools in final stage
# (use multi-stage builds)
```

---

## 16. Advanced Patterns

### Init Containers (Compose)

```yaml
services:
  db-init:
    image: postgres:15
    command: >
      sh -c "until pg_isready -h postgres -U mlflow; do sleep 1; done;
             psql -h postgres -U mlflow -c 'CREATE TABLE IF NOT EXISTS runs (...);'"
    depends_on:
      - postgres

  mlflow:
    depends_on:
      db-init:
        condition: service_completed_successfully
```

### Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health').raise_for_status()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s   # grace period for slow-starting services
```

### Dynamic Configuration with ARG

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ARG ENV=production
ENV APP_ENV=${ENV}

# Build for different environments:
# docker build --build-arg ENV=development -t ml-api:dev .
# docker build --build-arg ENV=production -t ml-api:prod .
```

### Docker in Docker (DinD) — for CI

```yaml
# CI pipeline that builds Docker images inside Docker
services:
  ci-runner:
    image: docker:24-dind
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

---

## 17. Docker in CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/ml-pipeline.yml
name: ML Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build test image
        run: docker build -t ml-pipeline:test --target test .

      - name: Run unit tests
        run: |
          docker run --rm ml-pipeline:test \
            pytest tests/unit/ -v --tb=short

      - name: Run integration tests
        run: |
          docker compose -f docker-compose.test.yml up --abort-on-container-exit
          docker compose -f docker-compose.test.yml down -v

  train-and-evaluate:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build training image
        run: docker build -t ml-train:${{ github.sha }} -f Dockerfile.train .

      - name: Run training
        run: |
          docker run \
            -e MLFLOW_TRACKING_URI=${{ secrets.MLFLOW_URI }} \
            -e AWS_ACCESS_KEY_ID=${{ secrets.AWS_KEY }} \
            -e AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET }} \
            ml-train:${{ github.sha }} \
            --epochs 50

  deploy:
    needs: train-and-evaluate
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker tag ml-api:latest $ECR_REGISTRY/ml-api:${{ github.sha }}
          docker push $ECR_REGISTRY/ml-api:${{ github.sha }}

      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster prod \
            --service ml-api \
            --force-new-deployment
```

---

## 18. GPU Support for Deep Learning

### Prerequisites

```bash
# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### PyTorch GPU Container

```dockerfile
# Use official CUDA + Python base image
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /train

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .

# No need to install CUDA — it's in the base image
CMD ["python", "train.py"]
```

```bash
# Run with GPU access
docker run --gpus all \
  -v $(pwd)/data:/data \
  my-pytorch-train:v1

# Use specific GPUs
docker run --gpus '"device=0,1"' my-train:v1

# Verify GPU access inside container
docker run --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### GPU in Compose

```yaml
# docker-compose.yml
services:
  trainer:
    build: .
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all     # or count: 1, or device_ids: ['0', '1']
              capabilities: [gpu]
    volumes:
      - ./data:/data
      - ./models:/models
```

### Popular Base Images for Deep Learning

```
pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime    # PyTorch + CUDA
tensorflow/tensorflow:2.14.0-gpu                  # TensorFlow + CUDA
nvcr.io/nvidia/tritonserver:23.10-py3             # NVIDIA Triton (serving)
huggingface/transformers-pytorch-gpu              # HuggingFace + PyTorch + GPU
```

---

## 19. Kubernetes Transition

Docker is the foundation — Kubernetes (K8s) orchestrates Docker containers at scale.

### Docker → Kubernetes Mapping

| Docker | Kubernetes |
|--------|------------|
| Container | Pod (wraps containers) |
| docker-compose.yml | Deployment YAML |
| docker run | kubectl apply |
| Named volume | PersistentVolume |
| Network | Service |
| Docker Hub | Container Registry |
| docker-compose scale | Horizontal Pod Autoscaler |

### Simple K8s Deployment (from Docker image)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ml-api
  template:
    metadata:
      labels:
        app: ml-api
    spec:
      containers:
        - name: ml-api
          image: myregistry/ml-api:v1.2.3
          ports:
            - containerPort: 8000
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          env:
            - name: MODEL_PATH
              value: "/models/model.pkl"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
```

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods
kubectl scale deployment ml-api --replicas=10
```

### When to Move from Compose to Kubernetes

- Need auto-scaling (traffic spikes)
- Need zero-downtime deployments
- Running in cloud (EKS, GKE, AKS)
- Need complex networking/service mesh
- Running multiple versions simultaneously (A/B testing)

---

## 20. Common Pitfalls

### 1. Using `:latest` Tag in Production

```bash
# BAD: unpredictable — latest changes silently
FROM python:latest
docker pull myimage:latest

# GOOD: pinned versions
FROM python:3.11.4-slim-bookworm
docker pull myimage:1.2.3
```

### 2. Storing Data in Containers

```bash
# BAD: data lost when container removed
docker run my-image  # writes to /data inside container
docker rm my-container  # ALL DATA GONE

# GOOD: use volumes
docker run -v my-volume:/data my-image
```

### 3. Building with Wrong Context

```bash
# BAD: sends entire / to Docker daemon
docker build /

# GOOD: build from project root with .dockerignore
cd /project && docker build .
```

### 4. Not Cleaning Up

```bash
# Prune unused containers, images, volumes, networks
docker system prune                    # removes stopped containers + dangling images
docker system prune -a                 # also removes unused images
docker system prune -a --volumes       # also removes unused volumes (CAREFUL)

# Individual cleanup
docker container prune
docker image prune -a
docker volume prune
```

### 5. Incorrect File Permissions

```bash
# Files created inside container may be owned by root
docker run -v $(pwd):/app my-image python generate.py
ls -la output/  # owned by root, can't edit on host!

# Fix: match container user ID to host user ID
docker run --user $(id -u):$(id -g) -v $(pwd):/app my-image python generate.py
```

### 6. Secrets in Build Args (visible in history)

```bash
# BAD: visible in docker history
docker build --build-arg API_KEY=secret .

# GOOD: use BuildKit secrets
docker build --secret id=api_key,env=API_KEY .
```

```dockerfile
# In Dockerfile with BuildKit:
RUN --mount=type=secret,id=api_key \
    API_KEY=$(cat /run/secrets/api_key) python download_model.py
```

---

## 21. Quick Reference Cheatsheet

### Lifecycle Commands

```bash
# Images
docker pull image:tag               # download image
docker build -t name:tag .          # build from Dockerfile
docker images                       # list images
docker rmi image:tag                # remove image
docker image prune -a               # remove unused images

# Containers
docker run [opts] image [cmd]       # create + start
docker start container              # start stopped container
docker stop container               # stop gracefully
docker kill container               # stop immediately
docker rm container                 # remove stopped container
docker ps                           # list running
docker ps -a                        # list all
docker logs -f container            # stream logs
docker exec -it container bash      # open shell
docker cp file container:/path      # copy file in
docker cp container:/path file      # copy file out
docker stats                        # resource usage

# Volumes
docker volume create name
docker volume ls
docker volume rm name
docker volume inspect name

# Networks
docker network create name
docker network ls
docker network inspect name

# Cleanup
docker system prune -a --volumes    # clean everything
```

### Common Run Patterns for Data Scientists

```bash
# Quick Python environment
docker run --rm -it -v $(pwd):/work -w /work python:3.11 bash

# Jupyter Lab with current directory
docker run --rm -p 8888:8888 -v $(pwd):/home/jovyan/work jupyter/scipy-notebook

# Run a Python script with requirements
docker run --rm -v $(pwd):/app -w /app python:3.11 \
  sh -c "pip install -r requirements.txt -q && python script.py"

# Quick database
docker run -d --name pg -e POSTGRES_PASSWORD=pass -p 5432:5432 postgres:15

# MLflow server backed by SQLite
docker run -d --name mlflow -p 5000:5000 \
  -v mlflow-data:/mlflow \
  python:3.11-slim \
  sh -c "pip install mlflow && mlflow server --host 0.0.0.0 --backend-store-uri /mlflow/mlflow.db"

# Model API with GPU
docker run --rm --gpus all -p 8000:8000 \
  -v $(pwd)/models:/models:ro \
  my-inference-api:v1
```

### Minimal Dockerfile Templates

```dockerfile
# Python Script
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```dockerfile
# FastAPI Service
FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# PyTorch GPU Training
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
WORKDIR /train
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
ENTRYPOINT ["python", "train.py"]
```

---

## Summary: When to Use Docker

| Scenario | Use Docker? | Why |
|----------|------------|-----|
| Sharing reproducible experiments | ✅ Yes | Exact environment snapshot |
| Local development with databases | ✅ Yes | No local install needed |
| Deploying ML models | ✅ Yes | Consistent prod/dev environments |
| Training on different GPU servers | ✅ Yes | Portable CUDA environments |
| CI/CD pipelines | ✅ Yes | Isolated, reproducible builds |
| Quick one-off scripts on your laptop | ⚡ Optional | virtualenv is simpler |
| Collaborating on a model | ✅ Yes | Eliminates "works on my machine" |
| Deploying to cloud (AWS/GCP/Azure) | ✅ Yes | Native support for containers |

---

*This guide covers Docker from zero to production-grade data science workflows.
Start with `docker run`, learn Dockerfile, then graduate to Compose for local stacks
and Kubernetes for production at scale.*
