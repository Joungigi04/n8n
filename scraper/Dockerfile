FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask selenium

WORKDIR /app
COPY scraper.py app.py /app/

EXPOSE 3000
CMD ["python", "app.py"]
