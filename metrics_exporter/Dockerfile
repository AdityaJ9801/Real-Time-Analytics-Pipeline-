FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    pymongo==4.6.0 \
    prometheus-client==0.19.0

COPY exporter.py .

CMD ["python", "-u", "exporter.py"]

