FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install flask pymongo flask_cors --no-cache-dir
CMD ["python", "-u", "app.py"]