FROM python:3.11-slim

# Prevent python from writing pyc files to disk and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY agent/ ./agent/

# Ensure PYTHONPATH is configured
ENV PYTHONPATH=/app/agent

# Entrypoint run command
ENTRYPOINT ["python", "agent/main.py"]
