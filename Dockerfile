FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (git for cloning, libpq-dev for postgres)
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Default command (will be overridden by docker-compose for specific services)
CMD ["streamlit", "run", "app.py"]
