FROM python:3.13-slim-bookworm

# Install git, required to install the alma_api_client package from github.
RUN apt-get update && \
    apt-get install -y git

# Set correct timezone
RUN ln -sf /usr/share/zoneinfo/America/Los_Angeles /etc/localtime

# Create generic ftva_etl user
RUN useradd -c "generic app user" -d /home/ftva_etl -s /bin/bash -m ftva_etl

# Switch to application directory, creating it if needed
WORKDIR /home/ftva_etl/project

# Make sure ftva_etl owns app directory, if WORKDIR created it:
# https://github.com/docker/docs/issues/13574
RUN chown -R ftva_etl:ftva_etl /home/ftva_etl

# Change context to ftva_etl user for remaining steps
USER ftva_etl

# Copy application files to image, and ensure ftva_etl user owns everything
COPY --chown=ftva_etl:ftva_etl . .

# Include local python bin into ftva_etl user's path, mostly for pip
ENV PATH=/home/ftva_etl/.local/bin:${PATH}

# Make sure pip is up to date, and don't complain if it isn't yet
RUN pip install --upgrade pip --disable-pip-version-check

# Install requirements for this application
RUN pip install --no-cache-dir -r requirements.txt --user --no-warn-script-location
