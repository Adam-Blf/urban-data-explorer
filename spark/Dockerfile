FROM bitnami/spark:3.5
USER root
RUN pip install --no-cache-dir polars psycopg2-binary pyarrow
COPY etl/ /opt/spark/etl/
COPY spark/jobs/ /opt/spark/jobs/
USER 1001
