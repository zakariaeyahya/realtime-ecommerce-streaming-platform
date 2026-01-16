FROM flink:1.18-scala_2.12-java11

# Install Python 3.10
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Symlink python3 to python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Install Flink Python dependencies
RUN pip install apache-flink==1.18.1

# Download and install Kafka connector JAR with retry logic
# This allows PyFlink to use FlinkKafkaConsumer and FlinkKafkaProducer
RUN mkdir -p /opt/flink/lib && \
    cd /opt/flink/lib && \
    for attempt in 1 2 3; do \
      echo "Download attempt $attempt..."; \
      if curl -f -L -o flink-connector-kafka-1.18.1.jar \
        https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka/1.18.1/flink-connector-kafka-1.18.1.jar; then \
        echo "Kafka connector downloaded successfully"; \
        break; \
      fi; \
      sleep 5; \
    done && \
    test -f flink-connector-kafka-1.18.1.jar || \
    echo "Warning: Could not download Kafka connector, continuing with basic Flink installation"

WORKDIR /flink
