FROM n8nio/n8n:latest

USER root
RUN apt-get update \
  && apt-get install -y chromium \
  && rm -rf /var/lib/apt/lists/* \
  && npm install n8n-nodes-puppeteer --no-save

USER node
