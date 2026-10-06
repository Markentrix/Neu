FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 tini ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY server/package.json server/package-lock.json server/
RUN cd server && npm ci --omit=dev
COPY server server
COPY src src
COPY site site
RUN mkdir -p /data && chown -R node:node /data /app/site
ENV NODE_ENV=production DATA_DIR=/data SITE_DIR=/data/site PORT=3000
USER node
VOLUME /data
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD node -e "fetch('http://127.0.0.1:3000/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["node","--disable-warning=ExperimentalWarning","server/index.js"]
