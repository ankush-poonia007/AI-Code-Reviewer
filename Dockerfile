# ==========================================================
# AI Code Reviewer
# Dockerfile v1
# ==========================================================

FROM python:3.11-slim

# -----------------------------
# Environment Configuration
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------
# Working Directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Install Dependencies
# -----------------------------
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Copy Application
# -----------------------------
COPY . .

# -----------------------------
# Expose FastAPI Port
# -----------------------------
EXPOSE 8000

# -----------------------------
# Start Application
# -----------------------------
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]