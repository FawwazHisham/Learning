# Tools, IDEs & Kubernetes — A Data Scientist's Clarity Guide

> Where do data scientists actually write code? Which tools, when, and why?

---

## Table of Contents

1. [The Big Picture — The Data Science Workflow](#1-the-big-picture--the-data-science-workflow)
2. [Jupyter Notebook — What It Really Is](#2-jupyter-notebook--what-it-really-is)
3. [JupyterLab — The Upgrade](#3-jupyterlab--the-upgrade)
4. [VS Code — The Most Popular Choice Today](#4-vs-code--the-most-popular-choice-today)
5. [PyCharm — The Python Powerhouse](#5-pycharm--the-python-powerhouse)
6. [Other Tools Worth Knowing](#6-other-tools-worth-knowing)
7. [Decision Guide — Which Tool When](#7-decision-guide--which-tool-when)
8. [How Docker Fits In](#8-how-docker-fits-in)
9. [When to Use Kubernetes (K8s)](#9-when-to-use-kubernetes-k8s)
10. [The Full Picture — A Real-World Stack](#10-the-full-picture--a-real-world-stack)

---

## 1. The Big Picture — The Data Science Workflow

Before picking tools, understand that data science work has **distinct phases** — and different tools serve different phases.

```
Phase 1: EXPLORATION          Phase 2: DEVELOPMENT         Phase 3: PRODUCTION
─────────────────────         ──────────────────────        ────────────────────
"What's in this data?"        "Build the real thing"        "Deploy & scale it"

  Jupyter Notebook              VS Code / PyCharm             Docker + K8s
  JupyterLab                    proper .py files              CI/CD pipelines
  Google Colab                  unit tests                    cloud services
  quick plots                   modular code                  monitoring

  Messy is OK here.             Clean code required.          Reliability required.
```

The mistake most beginners make: **using Jupyter for everything, including production code.**
The mistake some engineers make: **never using Jupyter and losing the exploratory advantage.**

---

## 2. Jupyter Notebook — What It Really Is

### What Is It?

Jupyter Notebook is a **web-based interactive computing environment** that runs in your browser. It combines:
- Code cells (Python, R, SQL, etc.)
- Markdown/text cells (documentation)
- Rich outputs (plots, tables, images, videos)

All in a single `.ipynb` file.

```
Browser (localhost:8888)
        │
        ▼
┌───────────────────────────────────────────────┐
│  Cell 1: [Markdown]  # Data Exploration       │
│  ─────────────────────────────────────────    │
│  Cell 2: [Code]                               │
│    import pandas as pd                        │
│    df = pd.read_csv("data.csv")               │
│    df.head()                                  │
│  ─────────────────────────────────────────    │
│  Output: [Table showing first 5 rows]         │
│  ─────────────────────────────────────────    │
│  Cell 3: [Code]                               │
│    df.describe()                              │
│  ─────────────────────────────────────────    │
│  Output: [Statistics table]                   │
└───────────────────────────────────────────────┘
        │
        ▼
Jupyter Server (Python kernel running in background)
```

### How It Works Under the Hood

```
Your Browser                  Jupyter Server              Python Kernel
─────────────                 ──────────────              ─────────────
You type code     ──────►     Receives code    ──────►    Executes it
                              via WebSocket               in memory
You see output    ◄──────     Sends back       ◄──────    Returns result
                              result
```

The **kernel** is a long-running Python process. Variables stay in memory between cells — that's what makes it interactive.

### Why Data Scientists Love Jupyter

```python
# You can explore data step by step
df = pd.read_csv("sales.csv")
df.head()                          # ← see output immediately, decide next step

# Then filter
df_2024 = df[df['year'] == 2024]
df_2024.shape                      # ← check shape before going further

# Then visualize
import matplotlib.pyplot as plt
df_2024['revenue'].plot(kind='bar')
plt.show()                         # ← plot renders right below the cell

# Then model
from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X_train, y_train)
print(f"R²: {model.score(X_test, y_test):.3f}")   # ← instant feedback
```

This **tight feedback loop** is invaluable for exploration. You don't need to re-run the whole script every time.

### When to Use Jupyter Notebook

```
✅ USE Jupyter when:
  - Exploring a new dataset for the first time
  - Doing EDA (Exploratory Data Analysis)
  - Creating visualizations and plots
  - Prototyping / experimenting with models
  - Writing data analysis reports (notebook = document)
  - Teaching or presenting (cells = slides with output)
  - Running one-off analyses
  - Sharing results with non-technical stakeholders

❌ AVOID Jupyter when:
  - Writing production code (functions, classes, pipelines)
  - Building reusable modules/packages
  - Writing unit tests
  - Code that needs to run in CI/CD pipelines
  - Large collaborative software projects
  - Long-running training jobs (use .py scripts instead)
```

### Jupyter Limitations (Know These)

```
1. Version control nightmare
   - .ipynb files are JSON with embedded outputs
   - Git diffs are unreadable
   - Merge conflicts are painful

2. Hidden state bugs
   Cell 1: x = 10
   Cell 2: x = 20         ← run this
   Cell 1 again: x = 10   ← now x is 10 again, but kernel still holds 20
   Cell 3: print(x)       ← prints 10... or 20? Depends on run order!

3. Not great for production
   - Hard to import functions from .ipynb files
   - No built-in testing framework
   - Can't easily run as a scheduled job (without nbconvert)

4. Performance
   - Heavy datasets slow the browser down
   - Not designed for distributed computing
```

### Running Jupyter

```bash
# Option 1: Install locally
pip install jupyter
jupyter notebook                    # opens at http://localhost:8888

# Option 2: Inside Docker (recommended for reproducibility)
docker run -p 8888:8888 \
  -v $(pwd):/home/jovyan/work \
  jupyter/scipy-notebook

# Option 3: Google Colab (zero setup, free GPU)
# https://colab.research.google.com
# — browser-based, Google's cloud, free T4 GPU

# Option 4: JupyterHub (for teams)
# Shared server where multiple users get their own Jupyter environments
```

---

## 3. JupyterLab — The Upgrade

JupyterLab is the **next-generation interface** for Jupyter. Think of it as Jupyter Notebook 2.0.

```
Jupyter Notebook                    JupyterLab
────────────────                    ──────────
Single notebook tab                 Multi-panel layout
No file browser (sidebar)          File browser + terminal + multiple notebooks
No text editor                     Built-in text editor for .py files
No terminal                        Integrated terminal
Older interface                    Modern, extensible UI
```

```bash
pip install jupyterlab
jupyter lab                         # opens at http://localhost:8888/lab
```

**JupyterLab layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  File  Edit  View  Run  Kernel  Settings  Help              │
├──────────┬──────────────────────────────────────────────────┤
│          │  Notebook 1.ipynb   │  terminal   │  data.csv   │
│ File     │─────────────────────│─────────────│─────────────│
│ Browser  │  [In]: import pd   │  $ ls data/ │  col1,col2  │
│          │  [Out]: DataFrame  │  train.csv  │  1,2        │
│ ──────── │                    │  test.csv   │  3,4        │
│ Tabs     │  [In]: df.plot()   │─────────────│─────────────│
│          │  [Out]: 📊 chart   │  utils.py   │             │
│ Running  │                    │  def clean: │             │
│ Kernels  │                    │    ...      │             │
└──────────┴──────────────────────────────────────────────────┘
```

**Use JupyterLab instead of Jupyter Notebook** — it's strictly better.

---

## 4. VS Code — The Most Popular Choice Today

### What Is VS Code?

VS Code (Visual Studio Code) is a **free, open-source code editor** by Microsoft. It's the most popular code editor in the world (Stack Overflow survey, every year since 2018).

It is NOT an IDE by default — it's a lightweight editor that becomes a full IDE through **extensions**.

### Why Data Scientists Use VS Code

```
1. Jupyter notebooks INSIDE VS Code
   - Edit .ipynb files natively
   - Better variable explorer than web Jupyter
   - Git integration works properly with notebooks

2. Python .py files with full IDE features
   - IntelliSense (autocomplete)
   - Go to definition (Ctrl+Click on any function)
   - Inline error highlighting
   - Refactoring tools

3. Integrated terminal
   - Run scripts, manage Docker, git — all in one window

4. Git integration
   - See diffs, stage changes, commit — without leaving the editor

5. Remote development
   - SSH into a remote server and code as if it's local
   - Connect to Docker containers directly
   - Connect to WSL (Windows Subsystem for Linux)

6. Extensions for everything
   - Python, Jupyter, Docker, GitHub Copilot, Pylance, Black formatter...
```

### Essential VS Code Extensions for Data Scientists

```
Extension               What It Does
──────────────────────  ─────────────────────────────────────────────
Python                  Core Python support, debugging, IntelliSense
Pylance                 Fast type checking, better autocomplete
Jupyter                 Run .ipynb notebooks natively in VS Code
Docker                  Manage containers/images from VS Code
Remote - SSH            Code on remote servers seamlessly
Remote - Containers     Code inside Docker containers
GitHub Copilot          AI pair programmer (autocomplete)
Black Formatter         Auto-format Python code
GitLens                 Enhanced git history and blame
Data Wrangler           Visual data exploration (like Excel, in VS Code)
Rainbow CSV             Color-code CSV columns for readability
```

### VS Code Workflow Example

```
Project structure:
my-project/
├── notebooks/
│   ├── 01_eda.ipynb          ← explore data here
│   └── 02_model_v1.ipynb     ← prototype model here
├── src/
│   ├── __init__.py
│   ├── features.py           ← clean code extracted from notebooks
│   ├── model.py              ← actual model class
│   └── utils.py
├── tests/
│   ├── test_features.py      ← unit tests
│   └── test_model.py
├── api/
│   └── main.py               ← FastAPI inference server
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

In VS Code you can have ALL of these open simultaneously:
- `01_eda.ipynb` in one tab (with live kernel)
- `features.py` in another tab (writing clean functions)
- Integrated terminal running `pytest tests/`
- Docker extension panel showing running containers

### When to Use VS Code

```
✅ USE VS Code when:
  - Writing production Python code (.py files)
  - Working on a project with multiple files
  - Need git integration daily
  - Need debugging (breakpoints, variable inspection)
  - Connecting to remote servers / Docker containers
  - Writing unit tests
  - Building APIs or pipelines
  - Working collaboratively (Live Share extension)
  - You want notebooks AND scripts in one tool
```

---

## 5. PyCharm — The Python Powerhouse

### What Is PyCharm?

PyCharm is a **full Python IDE** by JetBrains. It's heavier than VS Code but has more built-in Python-specific features.

```
VS Code                             PyCharm
───────                             ───────
Lightweight editor + extensions     Full IDE out of the box
Fast startup                        Slower startup (JVM-based)
Free, always                        Free (Community) / Paid (Professional)
Great for all languages             Python-first (best Python support)
Extensions can be unstable          Very stable, polished
Remote via extension                Remote via Professional edition
```

### When to Choose PyCharm over VS Code

```
✅ USE PyCharm when:
  - You work ONLY in Python (no JS, YAML editing, etc.)
  - You need the best Python refactoring tools
  - You're building large Python packages/libraries
  - Your team already uses JetBrains tools
  - You need built-in database IDE (Professional)
  - You need Jupyter + debugging integrated (Professional)

❌ Prefer VS Code when:
  - You work across multiple languages/file types
  - You want a lighter, faster editor
  - You're on a budget (PyCharm Pro is ~$250/year)
  - You need Docker/remote dev (VS Code Remote is better)
```

---

## 6. Other Tools Worth Knowing

### Google Colab (Free Cloud Notebooks)

```
What:   Google-hosted Jupyter notebooks in the cloud
Why:    Free GPU (T4/A100), zero setup, shareable link
When:   Quick experiments, learning, no local GPU
Limit:  Sessions time out, no persistent storage, limited RAM

URL: https://colab.research.google.com
```

```python
# In Colab, mount Google Drive for storage
from google.colab import drive
drive.mount('/content/drive')

# Free GPU — check what you have
!nvidia-smi
```

### Kaggle Notebooks (Free GPU for Competitions)

```
What:   Kaggle's hosted Jupyter environment
Why:    Free GPU, pre-loaded datasets, submit to competitions
When:   Kaggle competitions, learning from others' notebooks
URL:    https://kaggle.com/code
```

### Databricks Notebooks (Enterprise Scale)

```
What:   Cloud notebooks backed by Apache Spark clusters
Why:    Process terabytes of data, collaborative, enterprise-grade
When:   Big data, data engineering, enterprise ML platforms
Cost:   Paid (cloud compute), free community edition available
```

### RStudio (If You Use R)

```
What:   IDE specifically for R language
When:   Statistical analysis, R-based reporting, academic research
Note:   Python users typically skip this entirely
```

### Hex / Observable / Deepnote (Modern Notebooks)

```
What:   Next-gen collaborative notebook platforms
Why:    Better collaboration than Jupyter, built-in versioning
When:   Team data analysis, dashboards, modern data stack
Note:   Growing in popularity but not yet dominant
```

---

## 7. Decision Guide — Which Tool When

### The Honest Answer to "Where do Data Scientists write code?"

```
The answer is: it depends on the phase.

Phase 1 (Exploration)    →  Jupyter / JupyterLab / Colab
Phase 2 (Development)    →  VS Code (with Jupyter inside it)
Phase 3 (Production)     →  .py files in VS Code, run via Docker
```

### Decision Tree

```
Are you exploring data or prototyping?
├── YES → Use Jupyter / JupyterLab
│         (or Colab if you need free GPU or zero setup)
│
└── NO → Are you writing production/reusable code?
         ├── YES → Use VS Code or PyCharm
         │         (write proper .py files, not notebooks)
         │
         └── Are you on a team with enterprise data (TBs)?
             └── YES → Use Databricks or similar platform
```

### Practical Day-in-the-Life

```
9:00 AM  - New dataset arrives
           → Open JupyterLab, explore with pd.read_csv(), df.describe()

10:30 AM - Found interesting patterns, need to build a feature engineering function
           → Switch to VS Code, open src/features.py
           → Write clean, tested function
           → Import it back into notebook to verify

12:00 PM - Feature pipeline works, start model training script
           → Write train.py in VS Code
           → Run locally: python train.py

2:00 PM  - Need to share results with stakeholders
           → Back to Jupyter, create a clean notebook with plots + markdown
           → Or export to HTML: jupyter nbconvert --to html report.ipynb

3:30 PM  - Model ready, time to serve it
           → Write FastAPI app in VS Code
           → Containerize with Docker
           → Deploy
```

### The Modern Winning Setup (2025)

```
Tool                    Use For
──────────────────────  ─────────────────────────────────────
VS Code                 Primary editor — everything
  └─ Jupyter extension  Run notebooks inside VS Code
  └─ Remote SSH         Connect to GPU server or cloud VM
  └─ Dev Containers     Develop inside Docker containers
  └─ GitHub Copilot     AI autocomplete

JupyterLab (optional)  When you prefer the web UI for heavy EDA

Google Colab            Quick experiments, no local GPU

Docker                  Consistent environments, deployment

Git + GitHub            Version control, collaboration
```

---

## 8. How Docker Fits In

This connects the previous Docker guide to your daily workflow:

```
Your Laptop                          Docker Container
────────────                         ────────────────
VS Code (editor)         ────────►   Python 3.11 + all packages
  └─ Remote Containers               Your project files (mounted)
     extension                       Jupyter server

You edit code in VS Code,
but the code RUNS inside Docker.
No need to install Python, CUDA, or packages locally.
```

### Dev Containers — Code Inside Docker from VS Code

```json
// .devcontainer/devcontainer.json
{
  "name": "ML Dev Environment",
  "dockerComposeFile": "docker-compose.yml",
  "service": "notebook",
  "workspaceFolder": "/workspace",
  "extensions": [
    "ms-python.python",
    "ms-toolsai.jupyter",
    "ms-azuretools.vscode-docker"
  ],
  "postCreateCommand": "pip install -r requirements.txt"
}
```

After this setup:
1. Open VS Code
2. Click "Reopen in Container"
3. VS Code now runs INSIDE Docker — full IDE experience, containerized environment

---

## 9. When to Use Kubernetes (K8s)

### First — What Problem Does K8s Solve?

```
Docker:       Run one container on one machine.
Docker Compose: Run multiple containers on one machine.
Kubernetes:   Run many containers across MANY machines,
              automatically, reliably, at scale.
```

### The Scale Problem Docker Alone Can't Solve

```
Imagine your ML model API:

Monday morning:   100 users  → 1 Docker container is fine
Monday lunch:     5,000 users → 1 container is overwhelmed
Tuesday night:    50 users   → 1 container wastes resources

Docker can't:
  ✗ Automatically add more containers when traffic spikes
  ✗ Remove containers when traffic drops
  ✗ Recover if a server crashes
  ✗ Distribute load across multiple machines
  ✗ Deploy new version with zero downtime

Kubernetes CAN do all of the above.
```

### What Kubernetes Does

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                      │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │  Node 1  │   │  Node 2  │   │  Node 3  │   ← Machines  │
│  │ (server) │   │ (server) │   │ (server) │     (VMs)     │
│  │          │   │          │   │          │               │
│  │ [pod]    │   │ [pod]    │   │ [pod]    │               │
│  │ [pod]    │   │ [pod]    │   │ [pod]    │   ← Pods      │
│  │          │   │ [pod]    │   │          │     (containers)│
│  └──────────┘   └──────────┘   └──────────┘               │
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │           Control Plane                 │               │
│  │  - Schedules pods across nodes          │               │
│  │  - Auto-scales based on CPU/memory      │               │
│  │  - Restarts failed pods                 │               │
│  │  - Routes traffic to healthy pods       │               │
│  └─────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### When Data Scientists/ML Engineers Need K8s

```
✅ Use Kubernetes when:

1. SCALE — serving millions of predictions/day
   "Our model API needs to handle 10,000 requests/minute"

2. RELIABILITY — zero-downtime requirements
   "The model must be available 99.9% of the time"

3. PARALLEL TRAINING — running many experiments simultaneously
   "Run 50 hyperparameter search jobs in parallel on a GPU cluster"

4. RESOURCE MANAGEMENT — sharing GPUs across teams
   "10 data scientists, 20 GPUs — allocate fairly and efficiently"

5. ML PLATFORMS — using Kubeflow, MLflow on K8s, Seldon
   "Our company's ML platform runs on Kubernetes"

6. CLOUD ML — AWS SageMaker, GCP Vertex AI, Azure ML
   "These managed ML services are Kubernetes under the hood"

7. COST OPTIMIZATION — auto-scale down during off-peak hours
   "Don't pay for 100 servers at 3 AM when there's no traffic"
```

```
❌ Don't Use Kubernetes when:

- You're still exploring/prototyping (use Docker Compose)
- Your model serves < 100 requests/minute (Docker is enough)
- You're a solo data scientist (overkill)
- You don't have DevOps/MLOps support
- Your deadline is tomorrow (K8s has a steep learning curve)
```

### K8s Learning Path for Data Scientists

```
Stage 1: Understand Docker well         ← you're here now
Stage 2: Learn Docker Compose            ← multi-container local dev
Stage 3: Use a managed K8s service       ← AWS EKS, GCP GKE, Azure AKS
          (you don't manage the cluster, just deploy to it)
Stage 4: Learn kubectl basics            ← apply, get, describe, logs, exec
Stage 5: Learn Helm                      ← K8s package manager
Stage 6: Learn Kubeflow / MLflow on K8s  ← ML-specific K8s patterns
```

### Managed K8s for Data Scientists (The Practical Path)

You almost never set up K8s yourself. You use **managed services**:

```
Cloud Provider    Managed K8s     ML Platform on top
──────────────    ───────────     ──────────────────
AWS               EKS             SageMaker
Google Cloud      GKE             Vertex AI
Azure             AKS             Azure ML
On-premise        Rancher/OpenShift  Kubeflow
```

As a data scientist, you typically:
1. Build your Docker image
2. Push to a container registry (ECR, GCR, etc.)
3. Tell the ML platform "deploy this image"
4. The platform handles K8s scheduling, scaling, monitoring

### Minimum K8s You Should Know

```bash
# Check what's running
kubectl get pods
kubectl get services
kubectl get deployments

# Look at logs
kubectl logs pod-name
kubectl logs -f pod-name              # stream logs

# Get a shell inside a pod (like docker exec)
kubectl exec -it pod-name -- bash

# Deploy your model
kubectl apply -f deployment.yaml

# Scale your deployment
kubectl scale deployment ml-api --replicas=5

# Rolling update (zero downtime)
kubectl set image deployment/ml-api ml-api=myimage:v2
kubectl rollout status deployment/ml-api

# Rollback if something went wrong
kubectl rollout undo deployment/ml-api
```

### Real-World K8s ML Example

```yaml
# deployment.yaml — deploy your ML model API to K8s
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fraud-detection-api
spec:
  replicas: 3                    # start with 3 copies
  selector:
    matchLabels:
      app: fraud-detection
  template:
    spec:
      containers:
        - name: api
          image: myregistry/fraud-model:v1.2.3
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          env:
            - name: MODEL_PATH
              value: "/models/fraud_v3.pkl"

---
# Horizontal Pod Autoscaler — auto-scale based on CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fraud-detection-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fraud-detection-api
  minReplicas: 2
  maxReplicas: 20               # scale up to 20 pods automatically!
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

```
Traffic spikes →  CPU goes above 70% →  K8s adds more pods automatically
Traffic drops  →  CPU drops         →  K8s removes pods (min 2 always running)
```

---

## 10. The Full Picture — A Real-World Stack

Here is exactly how everything connects for a senior data scientist:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     YOUR DAILY WORKFLOW                             │
│                                                                     │
│  EXPLORATION                                                        │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  JupyterLab / VS Code + Jupyter extension           │           │
│  │  Running INSIDE Docker (consistent environment)     │           │
│  │  - pandas, scikit-learn, matplotlib, seaborn        │           │
│  │  - Connects to local Postgres/Redis via Compose     │           │
│  └─────────────────────────────────────────────────────┘           │
│                          │                                          │
│                          ▼                                          │
│  DEVELOPMENT                                                        │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  VS Code (editor)                                   │           │
│  │  - Write .py files: features.py, model.py, api.py  │           │
│  │  - Run tests: pytest tests/                         │           │
│  │  - Git commit & push                                │           │
│  └─────────────────────────────────────────────────────┘           │
│                          │                                          │
│                          ▼                                          │
│  CI/CD PIPELINE                                                     │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  GitHub Actions / GitLab CI                         │           │
│  │  - docker build → runs tests → docker push         │           │
│  │  - Triggered on every git push                      │           │
│  └─────────────────────────────────────────────────────┘           │
│                          │                                          │
│                          ▼                                          │
│  PRODUCTION                                                         │
│  ┌─────────────────────────────────────────────────────┐           │
│  │  Kubernetes (K8s)                                   │           │
│  │  - Runs your Docker container at scale              │           │
│  │  - Auto-scales: 2 pods at night, 50 pods at noon   │           │
│  │  - Restarts crashed pods automatically              │           │
│  │  - Zero-downtime deployments                        │           │
│  └─────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

### The Summary in One Sentence Per Tool

| Tool | One Sentence |
|------|-------------|
| **Jupyter/JupyterLab** | Your scratchpad for exploring data and prototyping models. |
| **VS Code** | Your primary editor for writing real, production-quality code. |
| **Google Colab** | Jupyter in the cloud, free GPU, zero setup — for experiments. |
| **Docker** | Packages your code + environment so it runs the same everywhere. |
| **Docker Compose** | Runs your whole local stack (Jupyter + DB + MLflow) with one command. |
| **Kubernetes** | Runs your Docker containers at scale across many machines in production. |

### Where to Start as a Senior Data Scientist

```
Week 1-2:   Get comfortable with JupyterLab for exploration
Week 3-4:   Set up VS Code as your primary editor, use it for .py files
Month 2:    Learn Docker — write Dockerfiles, use docker-compose for local dev
Month 3:    Add CI/CD — GitHub Actions to test and build Docker images
Month 4+:   Learn K8s basics when your models need to scale in production
```

---

*The most important insight: Jupyter is a scratchpad, not a production tool.
VS Code is where you build real software. Docker makes it portable.
K8s makes it scalable. Use each at the right phase.*
