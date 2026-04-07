# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright (headless browser)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    librandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    playwright \
    python-dotenv \
    openai \
    httpx

# Install Playwright browser engines (Chromium only for speed)
RUN playwright install chromium

# Copy the entire project (including the envs/ folder)
COPY . .

# Expose the standard HF Spaces port
EXPOSE 7860

# Command to run the standardized environment server
CMD ["python", "-m", "envs.prototype_env.server.app"]
