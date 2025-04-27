FROM n8nio/n8n:latest-node18-slim-chrome
RUN npm install n8n-nodes-puppeteer --no-save
