FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Run as a root user to resolve host volume mounting permission issues (staticfiles, migrations)
# RUN adduser --disabled-password --gecos '' appuser \
#     && chown -R appuser:appuser /app
# USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
