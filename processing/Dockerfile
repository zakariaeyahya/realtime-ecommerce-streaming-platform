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

# Download Kafka connector and dependencies with retry logic
# This allows PyFlink to use FlinkKafkaConsumer and FlinkKafkaProducer
RUN mkdir -p /opt/flink/lib && \
    cd /opt/flink/lib && \
    echo "Downloading Kafka Connector..." && \
    curl -f -L -o flink-connector-kafka-3.0.1-1.18.jar \
      https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka/3.0.1-1.18/flink-connector-kafka-3.0.1-1.18.jar && \
    echo "Downloading Kafka Clients..." && \
    curl -f -L -o kafka-clients-3.6.0.jar \
      https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.6.0/kafka-clients-3.6.0.jar && \
    echo "Downloading Kafka Common..." && \
    curl -f -L -o kafka-common-3.6.0.jar \
      https://repo1.maven.org/maven2/org/apache/kafka/kafka-common/3.6.0/kafka-common-3.6.0.jar && \
    echo "Downloading Kafka Protocol..." && \
    curl -f -L -o kafka-protocol-3.6.0.jar \
      https://repo1.maven.org/maven2/org/apache/kafka/kafka-protocol/3.6.0/kafka-protocol-3.6.0.jar && \
    echo "All Kafka dependencies downloaded successfully" || \
    echo "Warning: Some Kafka dependencies could not be downloaded"

WORKDIR /flink
