# scraper/Dockerfile
FROM python:3.11-slim

# zależności systemowe + Chromium + ChromeDriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Pythonowe biblioteki
RUN pip install flask selenium webdriver-manager

WORKDIR /app
COPY scraper/app.py /app/

EXPOSE 3000
CMD ["python", "app.py"]
