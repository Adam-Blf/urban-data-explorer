FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir kafka-python==2.0.2 requests==2.32.3 cassandra-driver==3.29.2
COPY streaming/ streaming/
# Default: run the Vélib GBFS producer.
# Override CMD to run the consumer:
#   docker compose run velib-producer python -m streaming.consumer
CMD ["python", "-m", "streaming.velib_producer"]
