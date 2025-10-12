# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Oracle
RUN apt-get update && apt-get install -y \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN wget https://download.oracle.com/otn_software/linux/instantclient/1918000/instantclient-basic-linux.x64-19.18.0.0.0dbru.zip \
    && unzip instantclient-basic-linux.x64-19.18.0.0.0dbru.zip \
    && rm instantclient-basic-linux.x64-19.18.0.0.0dbru.zip \
    && mv instantclient_19_18 /opt/oracle \
    && echo /opt/oracle > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]






