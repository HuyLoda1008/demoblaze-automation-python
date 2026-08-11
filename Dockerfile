# Base image tag must match the `playwright` pip version pinned in
# requirements.txt -- same discipline as the TypeScript sibling image.
FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY pyproject.toml ./
COPY config ./config
COPY src ./src
COPY tests ./tests

# No default args -- k8s CronJob manifests set them per environment (same
# "fail loudly if args are missing" rationale as the TypeScript image).
ENTRYPOINT ["python", "-m", "pytest"]
