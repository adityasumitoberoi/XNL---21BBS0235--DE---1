import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

# Kafka configuration
broker = 'localhost:9092'
topic = 'sensor_data'

# Initialize Kafka producer with JSON serializer
producer = KafkaProducer(
    bootstrap_servers=[broker],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print(f"Kafka Producer started, sending data to topic '{topic}'...")

try:
    while True:
        # Simulate sensor data
        sensor_id = f"sensor-{random.randint(1, 5)}"
        temperature = round(random.uniform(15.0, 30.0), 2)  # random temperature value
        timestamp = datetime.now().isoformat()
        data = {"sensor_id": sensor_id, "timestamp": timestamp, "temperature": temperature}
        
        # Send data to Kafka topic
        producer.send(topic, value=data)
        # Flush to ensure the message is sent
        producer.flush()
        
        print(f"Produced: {data}")
        # Wait for a second before sending the next reading
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping producer...")
finally:
    producer.close()
