# GitHub CI/CD Tutorial for This MLflow Repository

This tutorial teaches the basic CI/CD workflow using this repository as the example project. The repo contains a small Python machine learning workflow that trains a random forest model, logs parameters and metrics with MLflow, and saves run outputs as MLflow artifacts.

## What Students Will Learn

By the end of this tutorial, students should be able to:

- Explain what CI and CD mean in a machine learning project.
- Create a GitHub Actions workflow in `.github/workflows/`.
- Run a Python MLflow script automatically when code is pushed.
- Upload MLflow run outputs as workflow artifacts.
- Read a failed GitHub Actions log and identify which step failed.
- Understand how CI/CD supports reproducible machine learning work.

## Repository Overview

Important files in this repository:

- `requirements.txt`: Python dependencies used by the project.
- `scripts/mlflow_manual_logging.py`: Trains a random forest model and manually logs MLflow parameters, metrics, and the model artifact.
- `scripts/mlflow_autologging.py`: Trains a random forest model using MLflow autologging.
- `Notebooks/exploration.ipynb`: Exploration notebook.
- `scripts/mlruns/`: Example MLflow run history generated from previous runs.

The two scripts download the housing dataset, split the data, train a `RandomForestRegressor`, calculate RMSE values, and log results with MLflow.

## Core Concepts

### CI: Continuous Integration

Continuous Integration means every code change is checked automatically. In this repository, CI answers questions such as:

- Can GitHub create a clean Python environment?
- Can the dependencies in `requirements.txt` install successfully?
- Can the MLflow training scripts run from a fresh clone?
- Do the scripts produce MLflow output without crashing?

CI is useful because it checks the project on a clean machine, not just on one student's laptop.

### CD: Continuous Delivery or Deployment

Continuous Delivery means that after CI passes, the project produces something usable. Continuous Deployment means that the usable output is automatically released to users or infrastructure.

This repository does not contain a production API, web app, or package to deploy. For this tutorial, the CD step will publish the MLflow run directory as a GitHub Actions artifact. That artifact is the delivered output of the training run.

In a larger MLOps project, the CD step might instead:

- Register a model in a model registry.
- Build and push a Docker image.
- Deploy a model API to a cloud service.
- Publish documentation or reports.
- Trigger a batch prediction job.

### GitHub Actions Vocabulary

- Workflow: An automated process defined by a YAML file.
- Event: Something that starts a workflow, such as `push`, `pull_request`, or manual dispatch.
- Job: A group of steps that runs on the same machine.
- Runner: The machine that executes a job. In this tutorial, GitHub provides an Ubuntu runner.
- Step: One command or reusable action inside a job.
- Action: A reusable task, such as checking out code or setting up Python.
- Artifact: A file or folder saved from a workflow run so it can be downloaded later.
- Secret: A protected value, such as an API key or cloud credential.
- Status check: The pass/fail result that GitHub can show on commits and pull requests.

## Before You Start

Students need:

- A GitHub account.
- Git installed locally.
- Python 3.11 or newer installed locally.
- A copy or fork of this repository on GitHub.

Optional but useful:

- GitHub Desktop or the GitHub CLI.
- VS Code with the GitHub Pull Requests extension.

## Step 1: Run the Project Locally

Before automating a project, always run it manually once. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/mlflow_manual_logging.py --n_estimators 20 --max_depth 5
python scripts/mlflow_autologging.py --n_estimators 20 --max_depth 5
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Expected result:

- The scripts print train and test RMSE values.
- MLflow creates a local `mlruns/` folder if no tracking URI is configured.
- The scripts exit without errors.

If the scripts fail locally, fix the local issue before creating the GitHub Actions workflow.

## Step 2: Create a CI/CD Workflow File

GitHub Actions workflows live in `.github/workflows/`. Create this file:

```text
.github/workflows/mlflow-ci-cd.yml
```

From macOS, Linux, or Git Bash on Windows, create the folder and file with:

```bash
mkdir -p .github/workflows
touch .github/workflows/mlflow-ci-cd.yml
```

On Windows PowerShell, use:

```powershell
New-Item -ItemType Directory -Force -Path .github\workflows
New-Item -ItemType File -Force -Path .github\workflows\mlflow-ci-cd.yml
```

Paste the following workflow into it:

```yaml
name: MLflow CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  artifact-metadata: write

jobs:
  ci:
    name: CI - install and smoke test
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.11"]

    steps:
      - name: Check out repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run manual MLflow training smoke test
        env:
          MLFLOW_TRACKING_URI: file:./mlruns
        run: |
          python scripts/mlflow_manual_logging.py --n_estimators 20 --max_depth 5

      - name: Run autologging MLflow training smoke test
        env:
          MLFLOW_TRACKING_URI: file:./mlruns
        run: |
          python scripts/mlflow_autologging.py --n_estimators 20 --max_depth 5

      - name: Upload MLflow run artifact
        if: ${{ always() }}
        uses: actions/upload-artifact@v4
        with:
          name: mlflow-runs-${{ github.run_number }}
          path: mlruns/
          if-no-files-found: warn
          retention-days: 7

  cd:
    name: CD - publish training output
    runs-on: ubuntu-latest
    needs: ci
    if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}

    steps:
      - name: Download MLflow artifact
        uses: actions/download-artifact@v5
        with:
          name: mlflow-runs-${{ github.run_number }}
          path: delivered-mlruns

      - name: Write deployment summary
        run: |
          echo "Delivered MLflow run artifact for commit $GITHUB_SHA." >> "$GITHUB_STEP_SUMMARY"
          echo "Download it from the Artifacts section of this workflow run." >> "$GITHUB_STEP_SUMMARY"
```

## Step 3: Understand the Workflow

### Workflow Name

```yaml
name: MLflow CI/CD
```

This is the name shown in the GitHub Actions tab.

### Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

This workflow runs when:

- Someone pushes to `main`.
- Someone opens or updates a pull request targeting `main`.
- Someone starts it manually from the GitHub Actions page.

### Permissions

```yaml
permissions:
  contents: read
  artifact-metadata: write
```

This gives the workflow read-only access to the repository contents and permission to create artifact metadata. Start with the smallest permission set that works.

### CI Job

```yaml
jobs:
  ci:
```

The CI job creates a clean Linux environment, installs Python dependencies, and runs both MLflow scripts.

The key lesson: if a script only works on your laptop, CI will expose that. A healthy project should run from a clean clone.

### Runner

```yaml
runs-on: ubuntu-latest
```

This asks GitHub to run the job on a hosted Ubuntu machine.

### Matrix

```yaml
strategy:
  matrix:
    python-version: ["3.11"]
```

A matrix lets one workflow run across multiple versions or settings. For a class exercise, students can extend this to:

```yaml
python-version: ["3.10", "3.11", "3.12"]
```

### Checkout

```yaml
uses: actions/checkout@v6
```

This downloads the repository code into the runner. Without this step, the runner does not have the project files.

### Python Setup

```yaml
uses: actions/setup-python@v5
```

This installs and activates the requested Python version on the runner.

### Dependency Installation

```yaml
pip install -r requirements.txt
```

This recreates the Python environment from the dependency file. If a dependency is missing from `requirements.txt`, the workflow may fail even if the code works on a local machine.

### Smoke Tests

```yaml
python scripts/mlflow_manual_logging.py --n_estimators 20 --max_depth 5
python scripts/mlflow_autologging.py --n_estimators 20 --max_depth 5
```

These are smoke tests. A smoke test does not prove the model is good; it proves the main workflow can run successfully.

The workflow uses smaller hyperparameters than a real training run so CI finishes quickly.

### MLflow Tracking URI

```yaml
MLFLOW_TRACKING_URI: file:./mlruns
```

This tells MLflow to write run output to a local `mlruns/` folder inside the GitHub runner workspace. The folder is then uploaded as an artifact.

### Artifact Upload

```yaml
uses: actions/upload-artifact@v4
```

This stores the generated `mlruns/` folder after the job finishes. Artifacts are useful for logs, reports, model outputs, and other files produced during automation.

### CD Job

```yaml
cd:
  needs: ci
```

The CD job only runs after the CI job passes. In this tutorial, CD means the workflow delivers the MLflow output as an artifact and writes a summary to the workflow run page.

The condition below limits CD to direct pushes on `main`:

```yaml
if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
```

This prevents pull requests from publishing delivery outputs as if they were trusted main-branch runs.

## Step 4: Commit and Push the Workflow

From the repository root:

```bash
git checkout -b add-github-actions
git add README.md .github/workflows/mlflow-ci-cd.yml
git commit -m "Add GitHub Actions CI/CD tutorial"
git push origin add-github-actions
```

Then open a pull request on GitHub.

Important: if the repository still uses `master` instead of `main`, replace `main` in the workflow with `master`.

## Step 5: Watch the Workflow Run

On GitHub:

1. Open the repository.
2. Click the Actions tab.
3. Click the `MLflow CI/CD` workflow.
4. Open the newest run.
5. Expand each step in the CI job.

Students should identify:

- Which event started the run.
- Which branch or pull request triggered it.
- Which runner was used.
- How long dependency installation took.
- Where the model scripts printed RMSE values.
- Whether the MLflow artifact was uploaded.

## Step 6: Download the MLflow Artifact

After the workflow finishes:

1. Open the completed workflow run.
2. Scroll to the Artifacts section.
3. Download `mlflow-runs-<run-number>`.
4. Unzip the artifact locally.

This artifact contains the MLflow tracking directory produced by the CI run.

## Step 7: Test Failure Behavior

CI is most useful when students see it fail. Try one controlled failure on a separate branch:

1. Edit `requirements.txt`.
2. Temporarily remove `mlflow`.
3. Commit and push the change.
4. Open the failed workflow run.
5. Find the step that failed.
6. Restore `mlflow` in `requirements.txt`.
7. Commit and push the fix.

Expected lesson:

- The code may still exist, but the environment cannot run it without the dependency.
- The GitHub Actions log shows the failing command and error message.
- The pull request should not be merged until CI passes.

## Step 8: Use CI as a Pull Request Gate

For team projects, turn the workflow into a quality gate:

1. Go to the repository settings on GitHub.
2. Open Branches or Rulesets.
3. Add a rule for `main`.
4. Require the `MLflow CI/CD` status check to pass before merging.
5. Require pull requests instead of direct pushes.

This makes CI part of the collaboration process. Students can still make mistakes on branches, but `main` stays healthier.

## Step 9: Extend the Tutorial

Once the basic workflow works, students can extend it.

Useful extensions:

- Add `pytest` tests for data loading or metric calculation.
- Add `ruff` to check Python formatting and style.
- Run the matrix on multiple Python versions.
- Cache pip dependencies to speed up the workflow.
- Save a metrics summary file as an artifact.
- Build a Docker image for the training environment.
- Push a trained model to a real model registry.
- Deploy a small inference API after CI passes.

## Good CI/CD Habits for MLOps

- Keep workflow commands close to the commands used locally.
- Make CI fast enough that students actually wait for it.
- Use small smoke-test settings in CI.
- Store large datasets outside Git when possible.
- Treat generated MLflow runs as outputs, not source code, unless they are intentionally included for teaching.
- Use secrets for credentials; never hard-code API keys in scripts or workflow files.
- Give workflows only the permissions they need.
- Make pull requests pass CI before merging.

## Troubleshooting

### The workflow does not start

Check that the file is inside `.github/workflows/` and ends in `.yml` or `.yaml`.

### The workflow says the branch does not match

Check whether the default branch is `main` or `master`. Update the workflow trigger accordingly.

### Python dependencies fail to install

Run this locally:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If it fails locally, fix `requirements.txt` first.

### The scripts fail while downloading the dataset

The scripts currently load data from this URL:

```text
https://raw.githubusercontent.com/jbrownlee/Datasets/master/housing.csv
```

If the network request fails, rerun the workflow. For a more robust project, commit a small teaching dataset to the repo or add a data download step with retry logic.

### The artifact is missing

Check whether the scripts created `mlruns/`. Also check the `Upload MLflow run artifact` step in the workflow logs.

## Student Reflection Questions

1. Why is it useful to run this project on a clean GitHub runner?
2. What is the difference between CI and CD in this repository?
3. Why does the workflow use small model hyperparameters?
4. What would count as a real deployment for this MLflow project?
5. What should happen if a pull request fails CI?
6. Why should credentials be stored as GitHub secrets instead of being written in code?

## Official References

- GitHub Actions workflow syntax: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- GitHub Actions workflows overview: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows
- Building and testing Python with GitHub Actions: https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- Workflow artifacts: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts
