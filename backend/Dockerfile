# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /app

# Install system dependencies (OpenCV requires libgl1 and libglib2.0-0)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
# We use --no-build-isolation to prevent memory errors building torchvision/basicsr
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Copy the backend code
COPY . .

# Bake the model weights into the image (they are not in git).
RUN python scripts/download_weights.py

# Expose the application port
EXPOSE 8000

# Run the application
# start.sh runs `alembic upgrade head`, then uvicorn on $PORT (default 8000)
CMD ["./start.sh"]
