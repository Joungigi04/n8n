FROM n8nio/n8n:latest

USER root
RUN apk update && \
    apk add --no-cache \
      chromium \
      nss \
      freetype \
      harfbuzz \
      ttf-freefont && \
    npm install n8n-nodes-puppeteer --no-save

USER node