# CI/CD for Senior Data Scientists — Complete Guide

> From "what is CI/CD" to production ML pipelines with automated testing,
> model validation, and deployment — everything you need to know.

---

## Table of Contents

1. [What is CI/CD?](#1-what-is-cicd)
2. [Why Data Scientists Need CI/CD](#2-why-data-scientists-need-cicd)
3. [CI/CD vs Traditional Software vs ML](#3-cicd-vs-traditional-software-vs-ml)
4. [Core Concepts](#4-core-concepts)
5. [Git Workflow Foundation](#5-git-workflow-foundation)
6. [GitHub Actions — Deep Dive](#6-github-actions--deep-dive)
7. [Testing in Data Science](#7-testing-in-data-science)
8. [CI Pipeline for ML Projects](#8-ci-pipeline-for-ml-projects)
9. [CD — Deploying ML Models](#9-cd--deploying-ml-models)
10. [ML-Specific CI/CD — MLOps](#10-ml-specific-cicd--mlops)
11. [CI/CD for Notebooks](#11-cicd-for-notebooks)
12. [Secrets & Environment Management](#12-secrets--environment-management)
13. [CI/CD Tools Comparison](#13-cicd-tools-comparison)
14. [Advanced Patterns](#14-advanced-patterns)
15. [Real-World Complete Example](#15-real-world-complete-example)
16. [Common Pitfalls](#16-common-pitfalls)
17. [Quick Reference](#17-quick-reference)

---

## 1. What is CI/CD?

CI/CD stands for **Continuous Integration / Continuous Delivery (or Deployment)**.

It is the practice of **automating the process of testing, building, and deploying code** every time a change is made — instead of doing it manually.

### The Manual World (Before CI/CD)

```
Developer writes code
        ↓
"Works on my laptop"
        ↓
Manually run tests (sometimes skipped)
        ↓
Manually build Docker image
        ↓
SSH into server
        ↓
Manually copy files
        ↓
Manually restart the service
        ↓
Pray it works
        ↓
It doesn't work
        ↓
Spend 3 hours debugging "which version is running?"
```

### With CI/CD

```
Developer pushes code to Git
        ↓
CI/CD pipeline triggers AUTOMATICALLY
        ↓   ← this all happens without you doing anything
  ├── Run linting
  ├── Run unit tests
  ├── Run integration tests
  ├── Build Docker image
  ├── Push image to registry
  └── Deploy to production
        ↓
You get a notification: ✅ Deployed successfully (or ❌ Test failed)
```

### Breaking Down CI and CD

```
CI = Continuous Integration
─────────────────────────────
The "check" phase.
Every time code is pushed, automatically:
  - Run tests
  - Check code quality (lint, format)
  - Build the artifact (Docker image, package)
  - Catch problems BEFORE they reach production

CD = Continuous Delivery
─────────────────────────────
The artifact is always ready to deploy.
Deployment still requires MANUAL approval.
(Common in regulated industries: finance, healthcare)

CD = Continuous Deployment
─────────────────────────────
Every passing CI build is AUTOMATICALLY deployed.
No human approval needed.
(Common in fast-moving tech companies)
```

```
Push code
   │
   ▼
[CI: Build + Test]
   │
   ├── FAIL → notify developer, stop here
   │
   └── PASS
         │
         ▼ Continuous Delivery     ▼ Continuous Deployment
      [Artifact ready]          [Auto-deploy to prod]
      [Await approval]          [No human needed]
         │
         ▼
      [Manual deploy]
```

---

## 2. Why Data Scientists Need CI/CD

### The Data Science Problem Without CI/CD

```
Scenario: You trained a churn prediction model

Monday:   Model v1 deployed (accuracy: 82%)
Tuesday:  Colleague updates feature engineering code
Wednesday: You update the model
Thursday:  DevOps updates the API
Friday:    Nobody knows what version is running in production
Saturday:  Model accuracy drops to 67% — nobody knows why
```

### With CI/CD

```
Every change to code:
  → Automatically tested
  → Model performance validated against baseline
  → Docker image built with exact versions
  → Deployed only if ALL checks pass
  → Complete audit trail: who changed what, when, why
```

### Specific Benefits for Data Scientists

| Problem | CI/CD Solution |
|---------|---------------|
| "Works on my machine" | Docker build in CI catches environment issues |
| Untested code in production | Every PR must pass tests before merge |
| Unknown model version in prod | Each deployment tagged with git SHA + model hash |
| Slow manual deployment | One `git push` triggers everything |
| No rollback when model degrades | Previous Docker image always available |
| Experiment reproducibility | CI captures exact dependencies and data versions |
| Team collaboration conflicts | Automated merge checks catch integration issues |

---

## 3. CI/CD vs Traditional Software vs ML

### Traditional Software CI/CD

```
Code change → Tests pass? → Build → Deploy → Done

The artifact (binary/Docker image) is fully deterministic.
Same code = same behavior, always.
```

### ML CI/CD is harder because models are NOT deterministic

```
Code change → Tests pass? → Train model → Model good enough? → Deploy → Monitor
                                  ↑                ↑
                           depends on data    depends on metrics
                           (changes over time) (subjective threshold)
```

### The ML-Specific Challenges

```
1. DATA DEPENDENCY
   Code didn't change, but data changed → model behavior changes
   → Need data versioning (DVC) alongside code versioning (Git)

2. NON-DETERMINISM
   Same code + same data ≠ same model (random seeds, GPU ops)
   → Need to test behavior, not exact weights

3. SLOW TRAINING
   A CI pipeline running for 6 hours is unacceptable
   → Separate fast CI (code tests) from slow CD (training jobs)

4. PERFORMANCE VALIDATION
   "Does it compile?" is not enough — "Is accuracy > 80%?" matters
   → Need model evaluation as a CI gate

5. CONCEPT DRIFT
   Model degrades over time without any code change
   → Need continuous monitoring + retraining triggers
```

---

## 4. Core Concepts

### Pipeline

A pipeline is a **sequence of automated steps** triggered by an event.

```
Trigger: git push to main branch
    │
    ▼
Job 1: lint          ← check code style (fast, ~30s)
    │
    ▼
Job 2: test          ← run unit tests (medium, ~2min)
    │
    ▼
Job 3: build         ← build Docker image (~5min)
    │
    ▼
Job 4: integration   ← test the built image (~3min)
    │
    ▼
Job 5: deploy        ← push to production (~1min)
```

### Runner / Agent

The **machine that executes your pipeline steps**.

```
GitHub Actions:  "runner"       (GitHub's VMs or your own)
GitLab CI:       "runner"       (GitLab's or self-hosted)
Jenkins:         "agent"        (self-hosted)
CircleCI:        "executor"     (CircleCI's or self-hosted)

Runners can be:
  - GitHub-hosted (ubuntu-latest, windows-latest, macos-latest)
  - Self-hosted (your own server, GPU machine, on-premise)
```

### Artifact

**The output of a CI step** — passed to subsequent steps or stored.

```
Code → [build] → Docker image      ← artifact
Code → [train] → model.pkl         ← artifact
Code → [test]  → coverage report   ← artifact
Code → [build] → Python wheel      ← artifact
```

### Environment

```
dev     → developers test locally
staging → mirrors production, for final validation
prod    → real users, real traffic

CI/CD ensures: code passes through each environment
               before reaching production
```

---

## 5. Git Workflow Foundation

CI/CD is built on top of Git. You must understand branching strategy first.

### The Three Common Strategies

#### 1. GitHub Flow (simple, recommended for most ML projects)

```
main  ──────────────●──────────────●──────────────► (always deployable)
                    ↑              ↑
feature/add-lag-features        fix/memory-leak
     ●──●──●──●──(PR)──merge    ●──●──(PR)──merge

Rules:
  - main is ALWAYS deployable
  - All work happens on feature branches
  - Feature branches merge via Pull Request
  - CI runs on every PR
  - CD runs on merge to main
```

#### 2. GitFlow (complex, for versioned releases)

```
main         ──────────────────────────────────────►
              ↑                          ↑
            v1.0                       v2.0

develop  ─────●──────────────●──────────●──────────►
              ↑              ↑
feature/A  ●──●──merge    feature/B  ●──●──merge

release/1.0      ●──●──●──── (bugfixes only) ──────►

hotfix/critical     ●──merge to main AND develop
```

#### 3. Trunk-Based Development (fast teams, advanced CI/CD)

```
main  ●──●──●──●──●──●──●──●──►  (everyone commits directly)
            ↑
         feature flags hide incomplete features
         very short-lived branches (< 1 day)
```

### Recommended for Data Science Teams: GitHub Flow

```bash
# Daily workflow
git checkout -b feature/add-rfm-features
# ... work ...
git add src/features/rfm.py tests/test_rfm.py
git commit -m "feat: add RFM features for customer segmentation"
git push origin feature/add-rfm-features

# Open Pull Request on GitHub
# CI runs automatically:
#   ✅ lint passed
#   ✅ tests passed (87% coverage)
#   ✅ Docker build passed
# Colleague reviews and approves
# Merge → CD deploys automatically
```

### Commit Message Convention (Important for CI/CD)

```
<type>(<scope>): <description>

Types:
  feat:     new feature
  fix:      bug fix
  docs:     documentation only
  style:    formatting (no logic change)
  refactor: code restructuring
  test:     adding tests
  chore:    build tools, CI config changes
  perf:     performance improvement
  revert:   revert a commit

Examples:
  feat(model): add gradient boosting as alternative to random forest
  fix(features): handle missing values in age column
  test(api): add integration tests for /predict endpoint
  chore(ci): add model performance validation step
  perf(inference): reduce prediction latency by 40% with model quantization

Why this matters for CI/CD:
  - Conventional commits can AUTO-generate changelogs
  - Semantic versioning can be AUTOMATED from commit types
  - feat: → minor version bump (1.2.0 → 1.3.0)
  - fix:  → patch version bump (1.2.0 → 1.2.1)
  - BREAKING CHANGE: → major bump (1.2.0 → 2.0.0)
```

---

## 6. GitHub Actions — Deep Dive

GitHub Actions is the most popular CI/CD platform for data scientists because:
- Free for public repos, generous free tier for private
- Deeply integrated with GitHub (PRs, issues, releases)
- Huge marketplace of pre-built actions
- Native support for GPU runners (paid)

### File Structure

```
your-repo/
└── .github/
    └── workflows/
        ├── ci.yml          ← runs on every PR
        ├── cd.yml          ← runs on merge to main
        ├── train.yml       ← scheduled training job
        └── monitor.yml     ← scheduled model monitoring
```

### Anatomy of a Workflow File

```yaml
# .github/workflows/ci.yml

name: CI Pipeline                     # displayed on GitHub UI

on:                                   # TRIGGERS — when does this run?
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'              # daily at 2 AM UTC
  workflow_dispatch:                   # manual trigger button on GitHub

env:                                  # GLOBAL environment variables
  PYTHON_VERSION: "3.11"
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:                                 # JOBS — parallel by default
  lint:                               # job name (arbitrary)
    runs-on: ubuntu-latest            # runner type

    steps:                            # sequential steps within job
      - name: Checkout code
        uses: actions/checkout@v4     # pre-built action

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: pip install ruff black    # shell command

      - name: Lint with ruff
        run: ruff check src/

      - name: Check formatting
        run: black --check src/

  test:
    runs-on: ubuntu-latest
    needs: lint                       # wait for lint job to pass first

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'                # cache pip downloads between runs

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=term \
            -v

      - name: Upload coverage report
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Key GitHub Actions Concepts

#### Contexts — Access Metadata

```yaml
steps:
  - run: |
      echo "Repository: ${{ github.repository }}"       # owner/repo-name
      echo "Branch: ${{ github.ref_name }}"             # main, feature/xyz
      echo "Commit SHA: ${{ github.sha }}"              # abc123def456
      echo "Actor: ${{ github.actor }}"                 # username who triggered
      echo "Event: ${{ github.event_name }}"            # push, pull_request
      echo "Run ID: ${{ github.run_id }}"               # unique run identifier
```

#### Secrets — Secure Credentials

```yaml
# In GitHub: Settings → Secrets and variables → Actions → New secret
# Name: AWS_ACCESS_KEY_ID, Value: AKIAIOSFODNN7EXAMPLE

steps:
  - name: Configure AWS credentials
    uses: aws-actions/configure-aws-credentials@v4
    with:
      aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      aws-region: us-east-1
```

#### Matrix Strategy — Test Multiple Versions in Parallel

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]
        os: [ubuntu-latest, windows-latest]

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - run: pytest tests/

# This creates 6 parallel jobs:
# ubuntu + 3.9, ubuntu + 3.10, ubuntu + 3.11
# windows + 3.9, windows + 3.10, windows + 3.11
```

#### Caching — Speed Up Pipelines

```yaml
steps:
  - name: Cache pip packages
    uses: actions/cache@v3
    with:
      path: ~/.cache/pip
      key: pip-${{ runner.os }}-${{ hashFiles('requirements.txt') }}
      restore-keys: |
        pip-${{ runner.os }}-

  # Cache only invalidates when requirements.txt changes
  # Saves 2-3 minutes on typical data science project
```

#### Artifacts — Pass Files Between Jobs

```yaml
jobs:
  train:
    steps:
      - run: python train.py --output model.pkl

      - name: Upload trained model
        uses: actions/upload-artifact@v3
        with:
          name: trained-model
          path: model.pkl
          retention-days: 7

  evaluate:
    needs: train
    steps:
      - name: Download trained model
        uses: actions/download-artifact@v3
        with:
          name: trained-model

      - run: python evaluate.py --model model.pkl
```

#### Conditional Steps

```yaml
steps:
  - name: Deploy to production
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    run: ./deploy.sh prod

  - name: Deploy to staging
    if: github.event_name == 'pull_request'
    run: ./deploy.sh staging

  - name: Notify on failure
    if: failure()                   # only runs if previous step failed
    uses: slackapi/slack-github-action@v1
    with:
      payload: '{"text": "Pipeline failed!"}'
```

---

## 7. Testing in Data Science

Testing is the heart of CI. Without tests, CI is just "does it run?" not "does it work?".

### The Testing Pyramid for ML

```
                    ▲
                   /E2E\              ← End-to-end: full pipeline test
                  /─────\            ← few, slow, expensive
                 /integr-\
                /─────────\          ← Integration: components together
               /───────────\
              /  unit tests  \       ← Unit: individual functions
             /─────────────────\     ← many, fast, cheap
            └───────────────────┘
```

### Unit Tests for Data Science

```python
# tests/test_features.py
import pytest
import pandas as pd
import numpy as np
from src.features import compute_rfm, encode_categoricals, handle_missing

class TestComputeRFM:
    """Test RFM (Recency, Frequency, Monetary) feature computation."""

    def setup_method(self):
        """Create sample data used across tests."""
        self.df = pd.DataFrame({
            'customer_id': [1, 1, 2, 2, 2],
            'order_date': pd.to_datetime(['2024-01-01', '2024-02-01',
                                          '2024-01-15', '2024-02-15', '2024-03-01']),
            'amount': [100, 200, 50, 75, 25]
        })
        self.reference_date = pd.Timestamp('2024-04-01')

    def test_output_shape(self):
        """RFM should return one row per customer."""
        result = compute_rfm(self.df, self.reference_date)
        assert result.shape[0] == 2               # 2 unique customers
        assert result.shape[1] == 4               # customer_id + R + F + M

    def test_recency_calculation(self):
        """Recency should be days since last purchase."""
        result = compute_rfm(self.df, self.reference_date)
        customer_1 = result[result['customer_id'] == 1]
        # Last purchase was 2024-02-01, reference is 2024-04-01 → 59 days
        assert customer_1['recency'].values[0] == 59

    def test_frequency_calculation(self):
        """Frequency should be number of purchases."""
        result = compute_rfm(self.df, self.reference_date)
        customer_2 = result[result['customer_id'] == 2]
        assert customer_2['frequency'].values[0] == 3

    def test_monetary_calculation(self):
        """Monetary should be total spend."""
        result = compute_rfm(self.df, self.reference_date)
        customer_2 = result[result['customer_id'] == 2]
        assert customer_2['monetary'].values[0] == 150.0

    def test_empty_dataframe_raises(self):
        """Empty input should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            compute_rfm(pd.DataFrame(), self.reference_date)

    def test_no_nulls_in_output(self):
        """Output should never have null values."""
        result = compute_rfm(self.df, self.reference_date)
        assert result.isnull().sum().sum() == 0


class TestHandleMissing:
    """Test missing value handling."""

    def test_numerical_filled_with_median(self):
        df = pd.DataFrame({'age': [25, 30, np.nan, 40]})
        result = handle_missing(df)
        assert result['age'].isna().sum() == 0
        assert result['age'].iloc[2] == 30.0     # median of [25,30,40]

    def test_categorical_filled_with_mode(self):
        df = pd.DataFrame({'city': ['NYC', 'NYC', 'LA', None]})
        result = handle_missing(df)
        assert result['city'].isna().sum() == 0
        assert result['city'].iloc[3] == 'NYC'   # mode


class TestModelBehavior:
    """Test model predictions make business sense."""

    @pytest.fixture
    def trained_model(self):
        from src.model import ChurnModel
        import pickle
        with open("tests/fixtures/model.pkl", "rb") as f:
            return pickle.load(f)

    def test_predictions_in_valid_range(self, trained_model):
        """Churn probability must be between 0 and 1."""
        X = pd.read_csv("tests/fixtures/sample_features.csv")
        probs = trained_model.predict_proba(X)[:, 1]
        assert (probs >= 0).all() and (probs <= 1).all()

    def test_high_risk_customers_score_higher(self, trained_model):
        """Customers who never bought should have higher churn probability."""
        low_risk = pd.DataFrame({'recency': [5], 'frequency': [50], 'monetary': [5000]})
        high_risk = pd.DataFrame({'recency': [365], 'frequency': [1], 'monetary': [10]})

        low_score = trained_model.predict_proba(low_risk)[0, 1]
        high_score = trained_model.predict_proba(high_risk)[0, 1]

        assert high_score > low_score, "High-risk customer should score higher"

    def test_prediction_latency(self, trained_model):
        """Single prediction must complete under 100ms."""
        import time
        X = pd.read_csv("tests/fixtures/sample_features.csv").head(1)

        start = time.time()
        trained_model.predict(X)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 100, f"Prediction took {elapsed:.1f}ms, limit is 100ms"
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
import requests

BASE_URL = "http://localhost:8000"

class TestModelAPI:
    """Integration tests for the model serving API."""

    def test_health_endpoint(self):
        resp = requests.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_predict_valid_input(self):
        payload = {"recency": 30, "frequency": 5, "monetary": 1200.0}
        resp = requests.post(f"{BASE_URL}/predict", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "churn_probability" in data
        assert 0 <= data["churn_probability"] <= 1

    def test_predict_missing_field_returns_422(self):
        payload = {"recency": 30}   # missing frequency and monetary
        resp = requests.post(f"{BASE_URL}/predict", json=payload)
        assert resp.status_code == 422

    def test_predict_batch(self):
        payload = {"customers": [
            {"recency": 10, "frequency": 20, "monetary": 500},
            {"recency": 200, "frequency": 2, "monetary": 50},
        ]}
        resp = requests.post(f"{BASE_URL}/predict/batch", json=payload)
        assert resp.status_code == 200
        assert len(resp.json()["predictions"]) == 2
```

### Data Quality Tests (Great Expectations / Pandera)

```python
# tests/test_data_quality.py
import pandera as pa
from pandera import Column, DataFrameSchema, Check

# Define expected schema
training_data_schema = DataFrameSchema({
    "customer_id": Column(int, Check.greater_than(0)),
    "age": Column(float, [
        Check.greater_than_or_equal_to(18),
        Check.less_than_or_equal_to(120),
        Check(lambda x: x.isna().sum() / len(x) < 0.05,  # < 5% missing
              error="Too many missing values in age")
    ]),
    "churn": Column(int, Check.isin([0, 1])),
    "revenue": Column(float, Check.greater_than_or_equal_to(0)),
    "signup_date": Column("datetime64[ns]"),
})

def test_training_data_schema():
    """Validate training data meets expected schema."""
    import pandas as pd
    df = pd.read_parquet("data/processed/train.parquet")
    training_data_schema.validate(df)    # raises if validation fails

def test_no_data_leakage():
    """Ensure test set has no overlap with training set."""
    import pandas as pd
    train = pd.read_parquet("data/processed/train.parquet")
    test = pd.read_parquet("data/processed/test.parquet")

    train_ids = set(train['customer_id'])
    test_ids = set(test['customer_id'])

    overlap = train_ids & test_ids
    assert len(overlap) == 0, f"Data leakage: {len(overlap)} customers in both sets"

def test_class_balance():
    """Warn if class imbalance is extreme."""
    import pandas as pd
    df = pd.read_parquet("data/processed/train.parquet")
    churn_rate = df['churn'].mean()
    assert 0.01 <= churn_rate <= 0.99, f"Extreme class imbalance: {churn_rate:.1%} churn rate"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_features.py -v

# Run specific test
pytest tests/test_features.py::TestComputeRFM::test_recency_calculation -v

# Run fast tests only (mark slow tests with @pytest.mark.slow)
pytest tests/ -m "not slow"

# Run and stop at first failure
pytest tests/ -x

# Run in parallel (pip install pytest-xdist)
pytest tests/ -n auto
```

---

## 8. CI Pipeline for ML Projects

### Complete CI Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"

jobs:
  # ─── Job 1: Code Quality (fast, ~1 min) ───────────────────────────
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip

      - name: Install quality tools
        run: pip install ruff black mypy

      - name: Lint (ruff)
        run: ruff check src/ tests/

      - name: Format check (black)
        run: black --check src/ tests/

      - name: Type check (mypy)
        run: mypy src/ --ignore-missing-imports

  # ─── Job 2: Unit Tests (medium, ~3 min) ───────────────────────────
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: quality

    strategy:
      matrix:
        python-version: ["3.10", "3.11"]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-fail-under=80 \
            -v --tb=short

      - name: Upload coverage
        if: matrix.python-version == '3.11'
        uses: codecov/codecov-action@v3

  # ─── Job 3: Data Quality Tests ─────────────────────────────────────
  data-quality:
    name: Data Quality
    runs-on: ubuntu-latest
    needs: quality
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip

      - name: Restore cached data
        uses: actions/cache@v3
        with:
          path: data/
          key: data-${{ hashFiles('data/raw/.data_version') }}

      - name: Install dependencies
        run: pip install -r requirements.txt pandera

      - name: Run data validation
        run: pytest tests/data/ -v

  # ─── Job 4: Build Docker Image ─────────────────────────────────────
  build:
    name: Build Image
    runs-on: ubuntu-latest
    needs: [unit-tests, data-quality]
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha,prefix=sha-
            type=ref,event=pr
            type=ref,event=branch
            type=semver,pattern={{version}}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ─── Job 5: Integration Tests ──────────────────────────────────────
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: build

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Pull built image
        run: docker pull ${{ needs.build.outputs.image-tag }}

      - name: Start API server
        run: |
          docker run -d \
            --name api \
            --network host \
            -e DATABASE_URL=postgresql://postgres:testpass@localhost/testdb \
            ${{ needs.build.outputs.image-tag }}

      - name: Wait for API to be ready
        run: |
          for i in {1..30}; do
            curl -f http://localhost:8000/health && break
            sleep 2
          done

      - name: Run integration tests
        run: |
          pip install pytest requests
          pytest tests/integration/ -v

  # ─── Job 6: Security Scan ──────────────────────────────────────────
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Run Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ needs.build.outputs.image-tag }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'    # fail CI if critical vulnerabilities found

      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## 9. CD — Deploying ML Models

### Continuous Delivery Pipeline

```yaml
# .github/workflows/cd.yml
name: CD — Deploy

on:
  push:
    branches: [main]          # triggered only when CI passes on main

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: ml-models/churn-api

jobs:
  # ─── Deploy to Staging ─────────────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment: staging       # requires approval if configured

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, push to ECR
        id: push
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

      - name: Deploy to ECS (Staging)
        run: |
          aws ecs update-service \
            --cluster staging \
            --service churn-api \
            --task-definition churn-api-staging \
            --force-new-deployment

      - name: Wait for stable deployment
        run: |
          aws ecs wait services-stable \
            --cluster staging \
            --services churn-api

  # ─── Smoke Test Staging ────────────────────────────────────────────
  smoke-test-staging:
    name: Smoke Test Staging
    runs-on: ubuntu-latest
    needs: deploy-staging

    steps:
      - uses: actions/checkout@v4

      - name: Run smoke tests against staging
        env:
          API_URL: ${{ secrets.STAGING_API_URL }}
          API_KEY: ${{ secrets.STAGING_API_KEY }}
        run: |
          pip install pytest requests
          pytest tests/smoke/ -v \
            --base-url=$API_URL \
            --api-key=$API_KEY

  # ─── Deploy to Production (requires manual approval) ───────────────
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: smoke-test-staging
    environment: production     # ← set up required reviewers in GitHub UI

    steps:
      - name: Deploy to ECS (Production)
        run: |
          aws ecs update-service \
            --cluster production \
            --service churn-api \
            --task-definition churn-api-prod \
            --force-new-deployment

      - name: Tag release
        run: |
          git tag -a "v$(date +%Y%m%d%H%M%S)" -m "Production deployment ${{ github.sha }}"
          git push origin --tags

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Churn API deployed to production",
              "blocks": [{
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "*Deployed:* `churn-api` → production\n*Commit:* `${{ github.sha }}`\n*By:* ${{ github.actor }}"
                }
              }]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Rollback Strategy

```yaml
# .github/workflows/rollback.yml
name: Rollback Production

on:
  workflow_dispatch:
    inputs:
      target_tag:
        description: 'Docker image tag to rollback to'
        required: true
        type: string
      reason:
        description: 'Reason for rollback'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Rollback ECS to previous version
        run: |
          # Update task definition to point to the target image
          aws ecs update-service \
            --cluster production \
            --service churn-api \
            --task-definition churn-api-${{ inputs.target_tag }} \
            --force-new-deployment

      - name: Notify
        run: |
          echo "Rolled back to ${{ inputs.target_tag }}"
          echo "Reason: ${{ inputs.reason }}"
          # ... slack notification ...
```

---

## 10. ML-Specific CI/CD — MLOps

This is where ML CI/CD diverges from standard software CI/CD.

### The ML Pipeline as Code

```yaml
# .github/workflows/ml-pipeline.yml
name: ML Training Pipeline

on:
  push:
    paths:
      - 'src/**'            # trigger on code changes
      - 'configs/**'        # trigger on config changes
  schedule:
    - cron: '0 0 * * 0'    # retrain every Sunday at midnight
  workflow_dispatch:         # manual trigger

jobs:
  # ─── Step 1: Prepare Data ──────────────────────────────────────────
  prepare-data:
    runs-on: ubuntu-latest
    outputs:
      data-version: ${{ steps.version.outputs.hash }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup DVC
        uses: iterative/setup-dvc@v1

      - name: Pull data from remote
        run: |
          dvc remote modify myremote --local \
            access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}
          dvc pull data/raw/ --run-cache

      - name: Compute data version hash
        id: version
        run: |
          HASH=$(md5sum data/raw/*.parquet | md5sum | cut -d' ' -f1)
          echo "hash=$HASH" >> $GITHUB_OUTPUT

      - name: Validate data quality
        run: python src/validate_data.py

      - name: Run feature engineering
        run: python src/features.py

      - name: Upload processed data
        uses: actions/upload-artifact@v3
        with:
          name: processed-data
          path: data/processed/

  # ─── Step 2: Train Model ───────────────────────────────────────────
  train:
    runs-on: [self-hosted, gpu]     # use self-hosted GPU runner!
    needs: prepare-data

    steps:
      - uses: actions/checkout@v4

      - name: Download processed data
        uses: actions/download-artifact@v3
        with:
          name: processed-data
          path: data/processed/

      - name: Train model
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
          MLFLOW_EXPERIMENT_NAME: "churn-ci-${{ github.sha }}"
        run: |
          python src/train.py \
            --config configs/train_config.yaml \
            --run-name "ci-${{ github.sha }}" \
            --output-dir artifacts/

      - name: Upload model artifact
        uses: actions/upload-artifact@v3
        with:
          name: trained-model
          path: artifacts/
          retention-days: 30

  # ─── Step 3: Evaluate & Gate ───────────────────────────────────────
  evaluate:
    runs-on: ubuntu-latest
    needs: train

    steps:
      - uses: actions/checkout@v4

      - name: Download model
        uses: actions/download-artifact@v3
        with:
          name: trained-model
          path: artifacts/

      - name: Evaluate against test set
        run: python src/evaluate.py --model artifacts/model.pkl --output metrics.json

      - name: Check performance gate
        id: gate
        run: |
          python - <<'EOF'
          import json, sys

          with open("metrics.json") as f:
              metrics = json.load(f)

          thresholds = {
              "accuracy": 0.80,
              "f1_score": 0.75,
              "auc_roc": 0.82,
          }

          failed = []
          for metric, threshold in thresholds.items():
              value = metrics[metric]
              status = "✅" if value >= threshold else "❌"
              print(f"{status} {metric}: {value:.3f} (threshold: {threshold})")
              if value < threshold:
                  failed.append(f"{metric}={value:.3f} < {threshold}")

          if failed:
              print(f"\nFAILED: {', '.join(failed)}")
              sys.exit(1)
          else:
              print("\nAll performance gates passed!")
          EOF

      - name: Compare with production model
        run: |
          python src/compare_models.py \
            --new artifacts/model.pkl \
            --production s3://models/production/model.pkl \
            --output comparison.json

      - name: Fail if new model is worse
        run: |
          python - <<'EOF'
          import json, sys
          with open("comparison.json") as f:
              comp = json.load(f)
          if comp["new_model_wins"]:
              print("New model is better, proceeding with deployment")
          else:
              print(f"New model is WORSE: {comp['summary']}")
              sys.exit(1)
          EOF

      - name: Post metrics as PR comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const metrics = JSON.parse(fs.readFileSync('metrics.json'));
            const body = `## Model Performance Report
            | Metric | Value | Threshold | Status |
            |--------|-------|-----------|--------|
            | Accuracy | ${metrics.accuracy.toFixed(3)} | 0.80 | ${metrics.accuracy >= 0.80 ? '✅' : '❌'} |
            | F1 Score | ${metrics.f1_score.toFixed(3)} | 0.75 | ${metrics.f1_score >= 0.75 ? '✅' : '❌'} |
            | AUC-ROC | ${metrics.auc_roc.toFixed(3)} | 0.82 | ${metrics.auc_roc >= 0.82 ? '✅' : '❌'} |
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body
            });

  # ─── Step 4: Register Model ────────────────────────────────────────
  register:
    runs-on: ubuntu-latest
    needs: evaluate
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Download model
        uses: actions/download-artifact@v3
        with:
          name: trained-model
          path: artifacts/

      - name: Register in MLflow Model Registry
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
        run: |
          python - <<'EOF'
          import mlflow
          from mlflow.tracking import MlflowClient

          client = MlflowClient()

          # Register model
          model_uri = "runs:/${{ github.sha }}/model"
          mv = mlflow.register_model(model_uri, "churn-prediction")

          # Add tags
          client.set_model_version_tag(
              "churn-prediction", mv.version,
              "git_sha", "${{ github.sha }}"
          )
          client.set_model_version_tag(
              "churn-prediction", mv.version,
              "deployed_by", "ci-cd"
          )

          # Transition to Staging
          client.transition_model_version_stage(
              "churn-prediction", mv.version, "Staging"
          )
          print(f"Registered model version {mv.version} in Staging")
          EOF
```

### Model Monitoring Workflow

```yaml
# .github/workflows/monitor.yml
name: Model Monitoring

on:
  schedule:
    - cron: '0 8 * * *'    # daily at 8 AM

jobs:
  monitor:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Compute data drift
        run: |
          python src/monitoring/drift_detection.py \
            --reference data/reference/train_2024_01.parquet \
            --current data/production/predictions_last_7days.parquet \
            --output drift_report.json

      - name: Check for significant drift
        id: drift-check
        run: |
          python - <<'EOF'
          import json
          with open("drift_report.json") as f:
              report = json.load(f)

          if report["drift_detected"]:
              print(f"DRIFT DETECTED: {report['summary']}")
              print("::set-output name=drift::true")
          else:
              print("No significant drift detected")
              print("::set-output name=drift::false")
          EOF

      - name: Trigger retraining if drift detected
        if: steps.drift-check.outputs.drift == 'true'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.actions.createWorkflowDispatch({
              owner: context.repo.owner,
              repo: context.repo.repo,
              workflow_id: 'ml-pipeline.yml',
              ref: 'main',
              inputs: {
                trigger_reason: 'data_drift_detected'
              }
            });

      - name: Compute model performance on recent data
        run: |
          python src/monitoring/performance_monitoring.py \
            --model s3://models/production/model.pkl \
            --data data/production/labeled_last_7days.parquet \
            --output perf_report.json

      - name: Send daily report
        uses: slackapi/slack-github-action@v1
        with:
          payload-file-path: slack_payload.json
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 11. CI/CD for Notebooks

Notebooks are tricky for CI/CD because they contain embedded outputs and have hidden state.

### Problem: Notebooks in Git

```bash
git diff notebook.ipynb
# Output: massive JSON diff with base64-encoded images... unreadable
```

### Solution 1: Strip Output Before Committing

```bash
# Install nbstripout
pip install nbstripout

# Configure git to auto-strip notebook outputs on commit
nbstripout --install

# Now git diffs show only code changes, not output
```

### Solution 2: Convert Notebooks to Scripts (nbconvert)

```bash
# Convert notebook to Python script for CI testing
jupyter nbconvert --to script notebooks/eda.ipynb
# Creates: notebooks/eda.py

# Run in CI
python notebooks/eda.py
```

### Solution 3: Execute Notebooks in CI (papermill)

```yaml
# .github/workflows/notebook-ci.yml
name: Notebook CI

on:
  pull_request:
    paths:
      - 'notebooks/**'

jobs:
  run-notebooks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install -r requirements.txt papermill nbconvert

      - name: Execute EDA notebook
        run: |
          papermill notebooks/01_eda.ipynb \
                    notebooks/01_eda_executed.ipynb \
                    -p DATA_PATH data/sample_100rows.csv \
                    -p TEST_MODE true

      - name: Execute modeling notebook
        run: |
          papermill notebooks/02_modeling.ipynb \
                    notebooks/02_modeling_executed.ipynb \
                    -p MAX_ITER 5 \
                    -p QUICK_TEST true

      - name: Upload executed notebooks
        uses: actions/upload-artifact@v3
        with:
          name: executed-notebooks
          path: notebooks/*_executed.ipynb
```

### Solution 4: Use ReviewNB (GitHub App for Notebooks)

ReviewNB renders notebook diffs visually in GitHub PRs — shows what changed in plots, tables, text. Install from GitHub Marketplace.

---

## 12. Secrets & Environment Management

### Environment Variables Hierarchy

```
Priority (highest to lowest):
  1. Directly in workflow (hardcoded — avoid for secrets)
  2. GitHub Secrets (repository/organization level)
  3. .env file (local dev only, NEVER commit)
  4. Default values in code
```

### Managing Secrets in GitHub

```
Repository → Settings → Secrets and variables → Actions

Types:
  Repository secrets:    available to all workflows in this repo
  Organization secrets:  available to all repos in your org
  Environment secrets:   only available when deploying to that environment

Common secrets to configure:
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  MLFLOW_TRACKING_URI
  DATABASE_URL
  SLACK_WEBHOOK_URL
  DOCKER_REGISTRY_TOKEN
```

### Environment Files (Local Dev)

```bash
# .env (NEVER commit this)
MLFLOW_TRACKING_URI=http://localhost:5000
DATABASE_URL=postgresql://postgres:secret@localhost/mldb
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
MODEL_PATH=/models/churn_v3.pkl

# .env.example (commit this — template for teammates)
MLFLOW_TRACKING_URI=http://localhost:5000
DATABASE_URL=postgresql://user:password@localhost/dbname
AWS_ACCESS_KEY_ID=your-aws-key-here
AWS_SECRET_ACCESS_KEY=your-aws-secret-here
MODEL_PATH=/models/model.pkl
```

```python
# In your code — load .env for local dev
from dotenv import load_dotenv
import os

load_dotenv()   # loads .env file if it exists (ignored in CI)

DATABASE_URL = os.environ["DATABASE_URL"]         # fails loudly if missing
MODEL_PATH = os.environ.get("MODEL_PATH", "/models/default.pkl")  # has default
```

### Environment-Specific Configuration

```yaml
# configs/config.yaml
defaults:
  - _self_
  - env: dev               # default environment

env:
  dev:
    database_url: "sqlite:///dev.db"
    log_level: "DEBUG"
    batch_size: 32

  staging:
    database_url: "${oc.env:DATABASE_URL}"   # from environment variable
    log_level: "INFO"
    batch_size: 128

  prod:
    database_url: "${oc.env:DATABASE_URL}"
    log_level: "WARNING"
    batch_size: 512
```

```bash
# Use Hydra to switch environments
python train.py env=staging
python train.py env=prod
```

---

## 13. CI/CD Tools Comparison

### Side-by-Side Comparison

| Feature | GitHub Actions | GitLab CI | Jenkins | CircleCI |
|---------|---------------|-----------|---------|----------|
| **Setup** | Zero (hosted) | Zero (if SaaS) | Heavy (self-host) | Zero (hosted) |
| **Free tier** | 2000 min/month | 400 min/month | Free (self-host) | 6000 min/month |
| **GPU support** | Paid add-on | Self-hosted | Self-hosted | Paid add-on |
| **ML ecosystem** | Good | Good | Plugins only | Moderate |
| **Config** | YAML in `.github/` | YAML `.gitlab-ci.yml` | Groovy/GUI | YAML `.circleci/` |
| **Self-hosted** | Yes | Yes | Native | Yes |
| **Best for** | GitHub users | GitLab users | Enterprise on-prem | Flexibility |

### ML-Specific Platforms

| Platform | Purpose | When to Use |
|----------|---------|-------------|
| **Kubeflow Pipelines** | ML workflow orchestration on K8s | Large-scale ML on K8s |
| **MLflow + CI/CD** | Model tracking + deployment | Any scale |
| **AWS SageMaker Pipelines** | End-to-end ML on AWS | AWS-native teams |
| **Vertex AI Pipelines** | End-to-end ML on GCP | GCP-native teams |
| **DVC + CML** | Data versioning + ML reporting | Open-source stack |
| **Prefect / Airflow** | Data pipeline orchestration | Data engineering heavy |

### GitHub Actions is the Recommended Starting Point

```
Reasons:
  - If your code is on GitHub (most teams), it's already there
  - Zero infrastructure to manage
  - Largest marketplace of pre-built actions
  - Easy to read YAML syntax
  - Great for learning CI/CD fundamentals
  - Scales to enterprise with GitHub Enterprise
```

---

## 14. Advanced Patterns

### Self-Hosted GPU Runners

For training jobs, you need your own GPU machine as a runner:

```yaml
# Register your GPU machine as a GitHub Actions runner:
# GitHub Repo → Settings → Actions → Runners → New self-hosted runner
# Run the provided commands on your GPU machine

# Then target it in workflows:
jobs:
  train:
    runs-on: [self-hosted, gpu, linux]   # labels you assigned
    steps:
      - run: nvidia-smi    # verify GPU available
      - run: python train.py
```

### Reusable Workflows

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy

on:
  workflow_call:                         # makes this workflow reusable
    inputs:
      environment:
        required: true
        type: string
      image-tag:
        required: true
        type: string
    secrets:
      AWS_ACCESS_KEY_ID:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy ${{ inputs.image-tag }} to ${{ inputs.environment }}
        run: |
          aws ecs update-service \
            --cluster ${{ inputs.environment }} \
            --service churn-api
```

```yaml
# .github/workflows/cd.yml — calls the reusable workflow
jobs:
  deploy-staging:
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: staging
      image-tag: ${{ github.sha }}
    secrets:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}

  deploy-production:
    needs: deploy-staging
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
      image-tag: ${{ github.sha }}
    secrets:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
```

### A/B Testing Deployment

```yaml
jobs:
  deploy-ab-test:
    steps:
      - name: Deploy model v2 to 10% of traffic (canary)
        run: |
          # Update ECS service to run both v1 (90%) and v2 (10%)
          aws elbv2 modify-rule \
            --rule-arn ${{ secrets.ALB_RULE_ARN }} \
            --actions '[
              {"Type": "forward", "ForwardConfig": {
                "TargetGroups": [
                  {"TargetGroupArn": "${{ secrets.TG_V1_ARN }}", "Weight": 90},
                  {"TargetGroupArn": "${{ secrets.TG_V2_ARN }}", "Weight": 10}
                ]
              }}
            ]'

      - name: Monitor for 1 hour, then promote or rollback
        run: python scripts/canary_monitor.py --duration 3600 --threshold 0.01
```

### DVC + CML (Continuous Machine Learning)

DVC tracks data and models like Git tracks code. CML publishes ML reports to PRs.

```yaml
# .github/workflows/cml.yml
name: CML Report

on: [push]

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: iterative/setup-cml@v1

      - name: Train and report
        env:
          REPO_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          dvc pull
          python train.py

          # Generate report
          cat > report.md << 'EOF'
          ## Model Performance Report
          EOF

          python evaluate.py >> report.md

          # Add plots
          python - <<'PYEOF'
          import matplotlib.pyplot as plt
          # ... generate plots ...
          plt.savefig("roc_curve.png")
          PYEOF

          echo '![ROC Curve](./roc_curve.png)' >> report.md

          # Post report as PR comment
          cml comment create report.md
```

---

## 15. Real-World Complete Example

### Project Structure

```
churn-prediction/
├── .github/
│   └── workflows/
│       ├── ci.yml              ← runs on every PR
│       ├── cd.yml              ← deploys on merge to main
│       └── retrain.yml         ← weekly retraining
├── src/
│   ├── features.py
│   ├── model.py
│   ├── train.py
│   ├── evaluate.py
│   └── serve/
│       └── api.py
├── tests/
│   ├── unit/
│   │   ├── test_features.py
│   │   └── test_model.py
│   ├── integration/
│   │   └── test_api.py
│   └── smoke/
│       └── test_production.py
├── configs/
│   └── train_config.yaml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .dockerignore
├── .gitignore
└── dvc.yaml                    ← data pipeline definition
```

### The Full CI Flow on PR

```
Developer opens PR
        │
        ▼
GitHub Actions triggers ci.yml
        │
        ├── [1min]  quality: ruff + black + mypy
        │               │
        │               ▼ (parallel)
        ├── [3min]  unit-tests: pytest --cov=80%
        │               │
        │               ▼ (parallel)
        ├── [2min]  data-quality: pandera schema validation
        │               │
        │               ▼ (all must pass)
        ├── [5min]  build: docker build + push to ghcr.io
        │               │
        │               ▼ (parallel)
        ├── [3min]  integration: start container + test API
        │               │
        │               ▼ (parallel)
        └── [2min]  security: trivy vulnerability scan
                        │
                        ▼ (all must pass)
                    ✅ PR checks pass
                    Colleague reviews and approves
                    Merge to main
                        │
                        ▼
                    cd.yml triggers
                        │
                        ├── Deploy to staging (auto)
                        ├── Smoke test staging (auto)
                        ├── Await manual approval (production)
                        └── Deploy to production (manual)

Total time: ~15 minutes from push to production-ready
```

---

## 16. Common Pitfalls

### 1. Testing Against Production Data in CI

```yaml
# BAD: CI job downloads real production data (slow, expensive, privacy risk)
- run: aws s3 cp s3://prod-data/customers.parquet .

# GOOD: use a small, anonymized fixture
- run: cp tests/fixtures/sample_100_rows.parquet data/train.parquet
```

### 2. Not Caching Dependencies

```yaml
# BAD: pip install on every run (~3 min each time)
- run: pip install -r requirements.txt

# GOOD: cache pip packages
- uses: actions/setup-python@v4
  with:
    python-version: "3.11"
    cache: pip                 # adds ~2min savings per run
```

### 3. Hardcoding Secrets

```yaml
# BAD: secret visible in logs and git history!
- run: aws s3 cp model.pkl s3://bucket/ --access-key AKIAIOSFODNN7EXAMPLE

# GOOD: use secrets
- run: aws s3 cp model.pkl s3://bucket/
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
```

### 4. No Performance Gates

```yaml
# BAD: deploy any model that compiles
- run: python train.py

# GOOD: validate performance before deploying
- run: python train.py
- run: python evaluate.py --min-accuracy 0.80 --min-auc 0.82
```

### 5. Ignoring Flaky Tests

```bash
# Identify flaky tests
pytest tests/ --count=5    # run each test 5 times (pip install pytest-repeat)

# Fix flaky tests — common causes:
# - Random seeds not set
# - Tests depend on external APIs
# - Tests have shared state
# - Time-dependent assertions
```

### 6. Committing Generated Files

```gitignore
# .gitignore
*.pkl           # trained models
*.parquet       # data files
data/           # data directories
mlruns/         # MLflow artifacts
outputs/        # generated outputs
*.egg-info/     # Python package build artifacts
__pycache__/
.env
```

### 7. Not Testing the Docker Image Itself

```yaml
# BAD: only test code, not the container
- run: pytest tests/

# GOOD: also test the built container
- run: docker build -t myimage .
- run: docker run myimage pytest tests/  # tests run INSIDE container
```

---

## 17. Quick Reference

### GitHub Actions Trigger Cheatsheet

```yaml
on:
  push:                              # on any push
    branches: [main, develop]        # only these branches
    paths: ['src/**', '!docs/**']    # only if these paths changed

  pull_request:                      # on PR open/update
    branches: [main]                 # targeting main

  schedule:
    - cron: '0 2 * * 1'             # every Monday at 2 AM UTC
    #        min hour day month weekday
    #        0   2    *   *     1 (1=Monday)

  workflow_dispatch:                  # manual trigger button
    inputs:
      environment:
        type: choice
        options: [staging, production]

  release:
    types: [published]               # when a GitHub release is published
```

### Useful Actions from the Marketplace

```yaml
# Checkout code
- uses: actions/checkout@v4

# Setup Python with caching
- uses: actions/setup-python@v4
  with: { python-version: "3.11", cache: pip }

# Upload/download artifacts between jobs
- uses: actions/upload-artifact@v3
- uses: actions/download-artifact@v3

# Cache arbitrary directories
- uses: actions/cache@v3

# Build and push Docker images
- uses: docker/build-push-action@v5

# Configure AWS credentials
- uses: aws-actions/configure-aws-credentials@v4

# Login to ECR
- uses: aws-actions/amazon-ecr-login@v2

# Slack notification
- uses: slackapi/slack-github-action@v1

# Trivy security scan
- uses: aquasecurity/trivy-action@master

# Post PR comments
- uses: actions/github-script@v6
```

### Pipeline Duration Targets

```
Quality check (lint + types):     < 2 minutes
Unit tests:                        < 5 minutes
Docker build (with cache):         < 5 minutes
Integration tests:                 < 10 minutes
Total CI on PR:                    < 15 minutes  ← target
Model training (CD):               depends on model (use GPU runner)
Full CD to production:             < 30 minutes
```

### The ML CI/CD Maturity Model

```
Level 1 — Survival
  - Code in Git
  - Manual deployment

Level 2 — Basic CI
  - Automated tests on PR
  - Linting and formatting checks

Level 3 — CI + CD
  - Automated Docker builds
  - Automated deployment to staging
  - Manual approval for production

Level 4 — ML CI/CD
  - Training jobs in CI
  - Model performance gates
  - Model registry (MLflow)
  - Automated monitoring

Level 5 — Full MLOps
  - Automated retraining on drift
  - A/B testing deployments
  - Feature store integration
  - Lineage tracking (data → model → prediction)
  - Self-healing pipelines
```

---

*The core principle: every manual step is a bug waiting to happen.
CI/CD eliminates human error from your ML delivery process —
start simple (just tests), add automation layer by layer.*
