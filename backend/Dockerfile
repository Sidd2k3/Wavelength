# Wavelength backend — needs BOTH Python (FastAPI + ML) and Node.js
# (the Rettiwt fetcher that main.py runs as a subprocess every 30 min).
# We start from the Python image and install Node.js on top of it.

FROM python:3.11-slim

# Install Node.js 20 (for the fetcher) + build tools psycopg2 may need.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        build-essential \
        libpq-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the fetcher's Node dependencies.
COPY fetcher/package.json fetcher/package-lock.json ./fetcher/
RUN cd fetcher && npm install

# Copy the rest of the backend code.
COPY . .

# Render provides the port via $PORT. Start the FastAPI app with uvicorn.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
