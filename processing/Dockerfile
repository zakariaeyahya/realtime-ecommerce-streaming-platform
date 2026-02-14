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

# Download Kafka SQL connector (fat JAR - includes kafka-clients, no classloader conflicts)
RUN mkdir -p /opt/flink/lib && \
    cd /opt/flink/lib && \
    echo "Downloading Kafka SQL Connector (fat JAR)..." && \
    curl -f -L -o flink-sql-connector-kafka-3.0.1-1.18.jar \
      https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.0.1-1.18/flink-sql-connector-kafka-3.0.1-1.18.jar && \
    echo "Kafka SQL connector downloaded successfully" || \
    echo "Warning: Kafka connector could not be downloaded"

WORKDIR /flink
