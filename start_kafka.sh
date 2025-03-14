#!/bin/bash
# Script to start Apache Kafka and Zookeeper

# Ensure KAFKA_HOME is set to Kafka installation directory
if [ -z "$KAFKA_HOME" ]; then
  echo "Error: Please set KAFKA_HOME to your Kafka installation directory."
  exit 1
fi

# Start Zookeeper (if not already running)
echo "Starting Zookeeper..."
"$KAFKA_HOME/bin/zookeeper-server-start.sh" -daemon "$KAFKA_HOME/config/zookeeper.properties"

# Wait for Zookeeper to initialize
sleep 5

# Start Kafka broker
echo "Starting Kafka broker..."
"$KAFKA_HOME/bin/kafka-server-start.sh" -daemon "$KAFKA_HOME/config/server.properties"

echo "Kafka and Zookeeper startup initiated."
