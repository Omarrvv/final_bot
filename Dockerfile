FROM python:3.12-slim-bookworm

# Set environment variables to prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies including required build tools for C/C++ extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bzip2 \
    git \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    build-essential \
    gcc \
    g++ \
    cmake \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download and install Miniconda
RUN curl -fsSL -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-py312_24.3.0-0-Linux-aarch64.sh \
    && bash miniconda.sh -b -p /opt/miniconda \
    && rm miniconda.sh
ENV PATH=/opt/miniconda/bin:$PATH

# Add ARG declarations for build-time environment variables
ARG DATABASE_URL
ARG POSTGRES_DB
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_HOST
ARG POSTGRES_PORT

# Initialize Conda (makes `conda activate` work in subsequent RUN steps)
RUN conda init bash

# Copy environment and requirements files first
COPY environment.yml .
COPY requirements.txt . 

# Create conda environment from file with retry logic for network resilience
RUN bash -c "conda update -n base -c defaults conda && \
    (conda env create -f environment.yml || conda env create -f environment.yml || conda env create -f environment.yml) && \
    conda clean -afy"

# --- CONDA ENVIRONMENT ACTIVATION --- 
# Set the default shell to bash and activate conda env for subsequent RUN/CMD
# This makes RUN commands execute within the environment
SHELL ["conda", "run", "-n", "egypt-tourism1", "/bin/bash", "-c"]

# Copy application code
COPY . .

# --- DEPENDENCY INSTALLATION (within activated env) ---
# Install pip requirements with increased timeout and retry settings
RUN pip install --no-cache-dir --default-timeout=600 --retries 5 -r requirements.txt || \
    pip install --no-cache-dir --default-timeout=600 --retries 5 -r requirements.txt

# Download spacy models with retry logic and longer timeouts
RUN TIMEOUT=1200 && \
    (python -m pip install --default-timeout=$TIMEOUT --retries 10 https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl || \
     python -m pip install --default-timeout=$TIMEOUT --retries 10 https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl) && \
    (python -m pip install --default-timeout=$TIMEOUT --retries 10 https://github.com/explosion/spacy-models/releases/download/xx_ent_wiki_sm-3.8.0/xx_ent_wiki_sm-3.8.0-py3-none-any.whl || \
     python -m pip install --default-timeout=$TIMEOUT --retries 10 https://github.com/explosion/spacy-models/releases/download/xx_ent_wiki_sm-3.8.0/xx_ent_wiki_sm-3.8.0-py3-none-any.whl)

# Initialize database - Pass build args as env vars for this step
RUN export DATABASE_URL=${DATABASE_URL} && \
    export POSTGRES_DB=${POSTGRES_DB} && \
    export POSTGRES_USER=${POSTGRES_USER} && \
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD} && \
    export POSTGRES_HOST=${POSTGRES_HOST} && \
    export POSTGRES_PORT=${POSTGRES_PORT} && \
    python init_db.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 5050

# Default command - will be overridden by docker-compose, but good practice
CMD ["/opt/miniconda/envs/egypt-tourism1/bin/python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5050"]