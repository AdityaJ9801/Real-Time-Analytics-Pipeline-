FROM python:3.10-slim
WORKDIR /app
COPY producer.py .
RUN pip install kafka-python faker --no-cache-dir
CMD ["python", "-u", "producer.py"]