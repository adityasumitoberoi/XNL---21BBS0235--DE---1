
# IoT Data Ingestion Pipeline

## Overview
This project implements an IoT data ingestion pipeline using **Apache Kafka**, **PostgreSQL**, and **Apache Airflow**. It simulates IoT sensor readings, streams them via Kafka, stores them in a PostgreSQL database, and uses Airflow for daily ETL (Extract, Transform, Load) to aggregate the sensor data.

## Components
- **Kafka Producer (`producer.py`)** – Simulates IoT sensors by continuously sending random sensor data to a Kafka topic.
- **Kafka Consumer (`consumer.py`)** – Consumes data from Kafka and inserts it into a PostgreSQL database.
- **Airflow DAG (`etl_dag.py`)** – Defines a daily ETL workflow that extracts the previous day's data, calculates daily average metrics per sensor, and loads the results into an aggregation table.
- **PostgreSQL Schema (`sql_setup.sql`)** – SQL script to set up the database schema (tables for raw data and aggregated data).
- **Startup Scripts** – Shell scripts for convenience:
  - `start_kafka.sh` to start Kafka and Zookeeper (if running Kafka locally).
  - `start_airflow.sh` to initialize and start Airflow's scheduler and webserver.
- **Requirements (`requirements.txt`)** – Python dependencies for the project.
- **Docker Compose (`docker-compose.yml`)** – Docker Compose configuration for spinning up Kafka, Zookeeper, and PostgreSQL services easily.
- **Project Documentation (`README.md`)** – Setup and usage instructions (this file).

## Prerequisites
- Docker and Docker Compose (if you choose to use the provided `docker-compose.yml` for services).
- Python 3.x environment (if running the producer/consumer scripts on the host).
- Apache Kafka and Zookeeper (if not using Docker, ensure Kafka and Zookeeper are installed and configured).
- PostgreSQL database (if not using Docker, ensure a PostgreSQL server is running).
- Apache Airflow (for running the DAG, can be installed via pip or run in a container).

## Setup

### 1. Start Backend Services

**Using Docker Compose:**  
Run the following command to start Kafka, Zookeeper, and PostgreSQL in containers:
```bash
docker-compose up -d
```
This will launch:
- **Zookeeper** on port 2181.
- **Kafka** broker on port 9092 (advertised on `localhost:9092` for producer/consumer access).
- **PostgreSQL** on port 5432 with database `iot_db` (user: `iot_user`, password: `iot_password`).

*Verify* that the Docker containers are running with `docker-compose ps` and no errors appear in their logs.

**Without Docker (Manual):**  
- Start Zookeeper and Kafka using the `start_kafka.sh` script (requires Kafka installed locally and `KAFKA_HOME` environment variable set to your Kafka directory):
  ```bash
  chmod +x start_kafka.sh
  ./start_kafka.sh
  ```
  Ensure Kafka and Zookeeper processes are up (the script will run them as background daemons).
- Ensure PostgreSQL is running. Create a database (e.g., `iot_db`) and a user with credentials (e.g., `iot_user`/`iot_password`). Update the credentials in the Python scripts if you use different values, or create the user/password to match the defaults used in this project.

### 2. Set Up Database Schema
Use the provided SQL script to create the necessary tables in PostgreSQL:
```bash
psql -h localhost -U iot_user -d iot_db -f sql_setup.sql
```
This will create two tables:
- **`sensor_data`** – to store raw sensor readings (one row per reading).
- **`daily_sensor_stats`** – to store daily aggregated statistics (one row per sensor per day).

### 3. Install Python Dependencies
Install the required Python packages (preferably in a virtual environment) using:
```bash
pip install -r requirements.txt
```
This installs the Kafka client, PostgreSQL driver (psycopg2), and Airflow (among others). **Note:** If you prefer not to install Airflow globally via pip (since it can be heavy), you can run Airflow in Docker or manage it separately. The `requirements.txt` is provided for completeness.

### 4. Configure Apache Airflow
- Ensure Airflow is installed and its home directory is set (the default `AIRFLOW_HOME` is `~/airflow`).
- Initialize Airflow and create an admin user. You can use the provided script:
  ```bash
  chmod +x start_airflow.sh
  ./start_airflow.sh
  ```
  This will:
  - Initialize the Airflow metadata database (`airflow db init`).
  - Create an admin user with username `admin` and password `admin` (feel free to modify the script to change credentials).
  - Start the Airflow scheduler (in background) and webserver.
- Copy the `etl_dag.py` file into your Airflow DAGs directory (e.g., `~/airflow/dags/` if using the default setup). The DAG will be picked up by Airflow automatically.

Open the Airflow web UI (usually at [http://localhost:8080](http://localhost:8080)) and ensure the DAG **`daily_iot_etl`** is visible and not paused.

> **Note:** The DAG is scheduled to run daily at midnight (`@daily`) to process the previous day's data. For testing purposes, you can manually trigger the DAG from the Airflow UI or adjust the `schedule_interval` to `@once` or a more frequent interval.

## Running the Pipeline

1. **Start the Kafka Consumer:** In a terminal, run the consumer script to begin listening for incoming sensor data and writing it to the database.
   ```bash
   python consumer.py
   ```
   This will connect to the Kafka broker and subscribe to the `sensor_data` topic. You should see a log message indicating it connected to the database and is waiting for messages.

2. **Start the Data Producer:** In a separate terminal, run the producer script to start sending simulated sensor readings.
   ```bash
   python producer.py
   ```
   The producer will emit random sensor readings approximately once per second. Each message includes a sensor ID, a timestamp, and a temperature value. You will see output for each message produced.

3. **Verify Data Ingestion:** As the producer runs, the consumer should be receiving the messages and inserting them into PostgreSQL. You can connect to the database to verify:
   ```sql
   SELECT * FROM sensor_data LIMIT 5;
   ```
   You should see some rows of sensor data (sensor_id, timestamp, temperature). The consumer script also prints a confirmation each time it stores a record.

4. **Run the Airflow DAG:** If the time is past midnight (or the scheduled run time), Airflow will automatically trigger the **daily_iot_etl** DAG to process yesterday's data. For immediate testing, trigger the DAG manually via the Airflow UI (click "Trigger DAG"). The DAG will execute three tasks in order:
   - **Extract** – fetches all sensor records from the previous day from the `sensor_data` table.
   - **Transform** – calculates the average temperature and record count for each sensor for that day.
   - **Load** – inserts (or updates) a record in the `daily_sensor_stats` table for each sensor with the computed statistics.
   
   Monitor the DAG run in the Airflow UI to ensure it completes successfully.

5. **Check Aggregated Results:** After the DAG run, query the `daily_sensor_stats` table to see the aggregated data. For example:
   ```sql
   SELECT * FROM daily_sensor_stats;
   ```
   You should see entries like:
   ```
    date       | sensor_id | avg_temperature | count_records 
   ------------+-----------+-----------------+---------------
    2023-05-01 | sensor-1  | 22.5            | 86400
    2023-05-01 | sensor-2  | 19.8            | 86400
    ...
   ```
   (The above is an example structure; actual values will depend on the simulated data.)

## Notes
- The Kafka producer and consumer are configured to use `localhost:9092` as the Kafka bootstrap server. This works if Kafka is running locally or via Docker with ports exposed to the host. If you run the producer/consumer from within Docker or a different host, update the `broker` setting in both scripts (e.g., use `kafka:9092` if running within the same Docker network where the Kafka service is named "kafka").
- Ensure the PostgreSQL connection settings in `consumer.py` and `etl_dag.py` match your environment. The defaults are `host=localhost, database=iot_db, user=iot_user, password=iot_password`. If using Docker Compose as provided, these will work. If your Postgres is elsewhere or uses different credentials, adjust accordingly.
- To stop the pipeline: you can interrupt the producer and consumer scripts with `Ctrl+C`. If using Docker, you can shut down the Kafka/Zookeeper/Postgres services with:
  ```bash
  docker-compose down
  ```
  If running Kafka/Postgres manually, stop those services as you normally would.

- The Airflow scheduler and webserver can be stopped by terminating the processes started by `start_airflow.sh` (e.g., `Ctrl+C` in the webserver terminal, and stopping the scheduler by finding its process if needed). Alternatively, if using Airflow in Docker, stop the container.

## File Structure
```
├── producer.py          # Kafka producer script for generating sensor data
├── consumer.py          # Kafka consumer script for ingesting data into PostgreSQL
├── etl_dag.py           # Airflow DAG for daily aggregation ETL
├── sql_setup.sql        # SQL script to create database tables
├── start_kafka.sh       # Shell script to start Kafka and Zookeeper
├── start_airflow.sh     # Shell script to initialize and start Airflow
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker Compose configuration for Kafka, Zookeeper, Postgres
└── README.md            # Project documentation (this file)
```

With all components in place, this IoT data ingestion pipeline can be run end-to-end to simulate and process streaming sensor data. Follow the steps above to launch each part of the pipeline, and use the Airflow UI to monitor the ETL workflow.
