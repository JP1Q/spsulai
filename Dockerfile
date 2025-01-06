# Use the official Python image as a base
FROM python:3.9-slim

# Install dependencies required by MariaDB Connector/C and Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    mariadb-client \
    gcc \
    supervisor && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn

# Copy application files
COPY api-stuff/ /app/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 8052
EXPOSE 8053

# Run Supervisor to manage Uvicorn processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
