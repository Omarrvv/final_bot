FROM python:3.12-slim-bookworm

# Set environment variables to prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install curl, git, and other necessary system dependencies 
# (Miniconda installer needs bash, tar, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bzip2 \
    git \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    # Add build essentials if needed later for C extensions
    # build-essential \
    && rm -rf /var/lib/apt/lists/*

# Download and install Miniconda
RUN curl -fsSL -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-py312_24.3.0-0-Linux-aarch64.sh \
    && bash miniconda.sh -b -p /opt/miniconda \
    && rm miniconda.sh
ENV PATH=/opt/miniconda/bin:$PATH

# Initialize Conda (makes `conda activate` work in subsequent RUN steps)
RUN conda init bash

# Create conda environment from file (Run in bash to use conda init)
COPY environment.yml .
# Note: Running in a bash shell to ensure conda environment activation works
RUN bash -c "conda update -n base -c defaults conda && conda env create -f environment.yml && conda clean -afy"

# --- CONDA ENVIRONMENT ACTIVATION --- 
# Set the default shell to bash and activate conda env for subsequent RUN/CMD
# This makes RUN commands execute within the environment
SHELL ["conda", "run", "-n", "egypt-tourism1", "/bin/bash", "-c"]

# Copy application code
COPY . .

# --- DEPENDENCY INSTALLATION (within activated env) ---
# Install pip requirements
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy models
RUN python -m spacy download en_core_web_md && \
    python -m spacy download xx_ent_wiki_sm

# Initialize database 
RUN python init_db.py

# Set environment variables (PYTHONPATH might not be strictly needed with WORKDIR)
ENV PYTHONUNBUFFERED=1
# ENV PYTHONPATH=.

# Expose the port the app runs on
EXPOSE 5050

# Default command - will be overridden by docker-compose, but good practice
# Use the CMD from docker-compose for consistency
CMD ["/opt/miniconda/envs/egypt-tourism1/bin/python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5050"]
