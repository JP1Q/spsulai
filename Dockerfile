# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn

# Copy Python application files
COPY python_stuff/ /app/

# Install Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends supervisor && \
    rm -rf /var/lib/apt/lists/*


EXPOSE 8052
EXPOSE 8053

# Copy Supervisor configuration
COPY supervisord.conf /etc/supervisor/supervisord.conf

# Run Supervisor to manage the processes
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
