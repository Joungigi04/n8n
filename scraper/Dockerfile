# scraper/Dockerfile
FROM python:3.11-slim

# install system deps, chromium, chromedriver and needed libraries
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
 && rm -rf /var/lib/apt/lists/*

# tell Selenium where to find chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# install Python deps
RUN pip install --no-cache-dir flask selenium

WORKDIR /app
COPY scraper/app.py /app/

EXPOSE 3000

# use gunicorn in production for cleaner handling:
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:3000", "--workers", "1", "--threads", "1", "--log-level", "debug", "--capture-output"]
