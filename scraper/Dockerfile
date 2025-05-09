# scraper/Dockerfile
FROM python:3.11-slim

# Install OS deps for requests + BeautifulSoup
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask \
    requests \
    beautifulsoup4 \
    gunicorn

WORKDIR /app
COPY app.py /app/

EXPOSE 3000

# Run with Gunicorn
CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:3000", \
     "--workers", "1", "--threads", "1", \
     "--log-level", "debug", "--capture-output"]
