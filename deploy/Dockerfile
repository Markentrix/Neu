# ElbDetail – Anwendungsserver (Formulare, Verwaltungsportal, Statistik, Website-Generator)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ELB_DATA=/data \
    ELB_CONTENT=/data/content \
    ELB_CONTENT_SEED=/app/content-seed \
    ELB_SITE_ROOT=/srv/site \
    ELB_STATIC=/app/static \
    ELB_BUILDER=/app/build/build.py \
    HOST=0.0.0.0 \
    PORT=8080

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && useradd --system --uid 1000 --home /app elb \
 && mkdir -p /data /srv/site \
 && chown -R elb:elb /data /srv/site

WORKDIR /app
COPY --chown=elb:elb build/ build/
COPY --chown=elb:elb static/ static/
COPY --chown=elb:elb server/ server/
COPY --chown=elb:elb content/ content-seed/

USER elb
VOLUME ["/data", "/srv/site"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=4)"
CMD ["python3", "/app/server/app.py"]
