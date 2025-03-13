FROM docker.elastic.co/logstash/logstash:8.12.2

USER root

# Install curl for health check
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Create log directories
RUN mkdir -p /logs/transaction-service && \
    chown -R logstash:logstash /logs

USER logstash 