#!/bin/bash
# Script to initialize and start Apache Airflow (webserver & scheduler)

# Set Airflow home if not already set
export AIRFLOW_HOME=${AIRFLOW_HOME:-$HOME/airflow}

# Initialize Airflow database (if not done already)
airflow db init

# Create an Airflow admin user (if not exists)
# (Using default credentials: admin/admin for demonstration purposes)
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start the Airflow scheduler in the background
echo "Starting Airflow scheduler..."
airflow scheduler -D

# Start the Airflow webserver (will run in foreground)
echo "Starting Airflow webserver..."
airflow webserver
