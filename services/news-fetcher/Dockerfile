FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create state directory
RUN mkdir -p ./state

# Clear state files on container start
RUN echo '#!/bin/bash\n\
    # Clear state files\n\
    rm -f ./state/dedupe.json ./state/http_state.json\n\
    # Start the application\n\
    exec python -m src.main\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
