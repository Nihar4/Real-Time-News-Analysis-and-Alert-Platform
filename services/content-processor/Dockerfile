FROM python:3.13.5-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libpq-dev \
    librdkafka-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data for newspaper3k
RUN python -c "import nltk; nltk.download('punkt')"

# Copy source code
COPY src/ ./src/


# Run the service
CMD ["python", "-m", "src.main"]