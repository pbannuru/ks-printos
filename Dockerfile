FROM harbor.ext.hp.com/knowledge_search/python:3.12 AS build

# Update package list and install system dependencies with updates
RUN apt-get update && apt-get upgrade -y --no-install-recommends

# Set up the working directory
WORKDIR /app

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/env
RUN . /opt/env/bin/activate && \
    pip install --no-cache-dir --disable-pip-version-check -r requirements.txt --no-deps
COPY my-root-ca.crt /tmp/my-root-ca.crt    
RUN cat /tmp/my-root-ca.crt >> /opt/env/lib/python3.12/site-packages/certifi/cacert.pem

# Stage 2: Runtime
FROM harbor.ext.hp.com/knowledge_search/python:3.12 AS runtime

# Update package list and install necessary dependencies
RUN apt-get update && apt-get upgrade -y --no-install-recommends

# Set up the working directory
WORKDIR /app

# Copy the build environment from the build stage
COPY --from=build /app /app
COPY . .

# Copy Python environment from the build stage
COPY --from=build /opt /opt

# CMD . /opt/env/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8092
# CMD . /opt/env/bin/activate && gunicorn -k uvicorn.workers.UvicornWorker app.main:app --workers 2 --bind 0.0.0.0:8092

CMD . /opt/env/bin/activate && \
    gunicorn -k uvicorn.workers.UvicornWorker app.main:app \
    --workers $(( $(nproc --all) * 2 )) \
    --threads $(( $(nproc --all) * 2 )) \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --bind 0.0.0.0:8092