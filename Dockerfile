# ── Dockerfile ─────────────────────────────────────────────────────────────
# Packages the entire EduForAll app into a Docker container so it runs
# the same way on any machine — no "it works on my machine" issues.
#
# Build the image:
#   docker build -t eduforall .
#
# Run the container:
#   docker run -p 8501:8501 eduforall
#
# Then open: http://localhost:8501

# ── Base Image ──────────────────────────────────────────────────────────────
# Use the official lightweight Python 3.11 image (stable, widely supported)
# We use 3.11 here for maximum library compatibility inside Docker
FROM python:3.11-slim

# ── Metadata ────────────────────────────────────────────────────────────────
LABEL maintainer="TIA WOUMLACK ARIEL BLERIO"
LABEL description="EduForAll — Personalized learning for students with disabilities"
LABEL version="1.0"

# ── Working Directory ────────────────────────────────────────────────────────
# All commands from here on run inside /app inside the container
WORKDIR /app

# ── System Dependencies ──────────────────────────────────────────────────────
# Install minimal system packages needed to build Python libraries
# --no-install-recommends keeps the image small
RUN apt-get update && apt-get install -y \
    build-essential \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# ── Copy Requirements First ──────────────────────────────────────────────────
# We copy requirements.txt before the rest of the code.
# This is a Docker best practice: if requirements don't change,
# Docker reuses the cached layer and skips reinstalling — faster builds.
COPY requirements.txt .

# ── Install Python Dependencies ──────────────────────────────────────────────
# --no-cache-dir keeps the image size small by not caching downloaded packages
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy Application Code ────────────────────────────────────────────────────
# Copy all project files into the container's /app directory
COPY . .

# ── Create Data Directory ────────────────────────────────────────────────────
# Ensure the data folder exists inside the container
RUN mkdir -p data

# ── Expose Port ──────────────────────────────────────────────────────────────
# Streamlit runs on port 8501 by default
# EXPOSE tells Docker which port the container listens on
EXPOSE 8501

# ── Streamlit Configuration ──────────────────────────────────────────────────
# Disable the browser auto-open and set server settings for container use
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# ── Start Command ────────────────────────────────────────────────────────────
# This is the command Docker runs when the container starts
# It launches the Streamlit app on all interfaces (0.0.0.0) so it's
# accessible from outside the container
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
