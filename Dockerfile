# 1) Bazujemy na oficjalnym obrazie n8n (to Alpine)
FROM n8nio/n8n:latest

# 2) Przełączamy się na roota, żeby móc zainstalować paczki
USER root

# 3) Instalujemy Chromium i zależności oraz community-node Puppeteer
RUN apk update && \
    apk add --no-cache \
      chromium \
      nss \
      freetype \
      harfbuzz \
      ttf-freefont && \
    npm install n8n-nodes-puppeteer --no-save

# 4) Wracamy do użytkownika node (domyślny)
USER node
