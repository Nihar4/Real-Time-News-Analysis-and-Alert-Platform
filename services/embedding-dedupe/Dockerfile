FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2 and git (if needed for pip packages)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Run the service
CMD ["python", "-m", "src.main"]
