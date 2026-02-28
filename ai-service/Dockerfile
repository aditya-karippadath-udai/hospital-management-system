# Use NVIDIA CUDA base for GPU support
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and essentials
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_MODULE=app.main:app

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI with Gunicorn/Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
