FROM continuumio/miniconda3:latest

WORKDIR /app

# Create conda environment
COPY environment.yml .
RUN conda update -n base -c defaults conda && \
    conda env create -f environment.yml && \
    conda clean -afy

# Remove the global SHELL activation
# SHELL ["conda", "run", "-n", "egypt-tourism1", "/bin/bash", "-c"]

# Install build tools first using conda within the environment
# Use appropriate package names for the target architecture (aarch64 for Apple Silicon)
RUN conda run -n egypt-tourism1 conda install -y gcc_linux-aarch64 gxx_linux-aarch64

# Copy application code
COPY . .

# Install pip requirements WITHIN the correct conda env explicitly
# Force conda install for key scientific packages first to ensure library compatibility
RUN conda run -n egypt-tourism1 conda install -y scipy scikit-learn && \
    conda run -n egypt-tourism1 pip install --no-cache-dir -r requirements.txt

# Download spacy models using explicit conda run
RUN conda run -n egypt-tourism1 python -m spacy download en_core_web_md && \
    conda run -n egypt-tourism1 python -m spacy download xx_ent_wiki_sm

# Initialize database using explicit conda run
RUN conda run -n egypt-tourism1 python init_db.py

# Set environment variables
ENV PYTHONPATH=. \
    PYTHONUNBUFFERED=1

# Expose the port Uvicorn will use
EXPOSE 5050

# Default command can be empty, as docker-compose provides it
CMD []
