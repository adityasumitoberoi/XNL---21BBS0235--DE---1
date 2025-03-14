import json
import psycopg2
from datetime import datetime
from kafka import KafkaConsumer

# Kafka and Database configuration
broker = 'localhost:9092'
topic = 'sensor_data'
group_id = 'iot-group'

db_config = {
    "host": "localhost",
    "database": "iot_db",
    "user": "iot_user",
    "password": "iot_password"
}

# Initialize Kafka consumer with JSON deserializer
consumer = KafkaConsumer(
    topic,
    bootstrap_servers=[broker],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id=group_id,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Connect to PostgreSQL database
conn = psycopg2.connect(**db_config)
cur = conn.cursor()
print(f"Connected to PostgreSQL database {db_config['database']} and listening to Kafka topic '{topic}'...")

try:
    for message in consumer:
        # message.value will be a dict as we serialized in JSON
        data = message.value
        sensor_id = data.get('sensor_id')
        ts_str = data.get('timestamp')
        temperature = data.get('temperature')
        try:
            # Convert timestamp string to datetime object
            ts = datetime.fromisoformat(ts_str) if ts_str else None
        except Exception:
            ts = None
        
        # Insert data into PostgreSQL
        cur.execute(
            "INSERT INTO sensor_data (sensor_id, timestamp, temperature) VALUES (%s, %s, %s)",
            (sensor_id, ts, temperature)
        )
        conn.commit()
        print(f"Consumed and stored: {data}")
except KeyboardInterrupt:
    print("Stopping consumer...")
finally:
    # Close database connection on exit
    cur.close()
    conn.close()
    consumer.close()
