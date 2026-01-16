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

WORKDIR /flink
