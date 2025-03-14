from datetime import datetime, timedelta, date
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator

# Database connection configuration
DB_CONFIG = {
    "host": "localhost",
    "database": "iot_db",
    "user": "iot_user",
    "password": "iot_password"
}

def extract_data(**kwargs):
    """Extract yesterday's sensor data from PostgreSQL."""
    target_date = (datetime.now() - timedelta(days=1)).date()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    # Fetch all records from yesterday
    cur.execute("SELECT sensor_id, temperature FROM sensor_data WHERE DATE(timestamp) = %s;", (target_date,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Prepare data for XCom (as list of dicts for JSON serialization)
    data = [{"sensor_id": r[0], "temperature": float(r[1])} for r in rows]
    return {"date": target_date.strftime("%Y-%m-%d"), "data": data}

def transform_data(**kwargs):
    """Transform data by calculating average temperature and count per sensor for the date."""
    ti = kwargs.get('ti')  # Task instance from Airflow context
    dataset = ti.xcom_pull(task_ids='extract')
    if not dataset:
        return None
    date_str = dataset.get("date")
    data = dataset.get("data", [])
    # Aggregate by sensor_id
    agg_results = {}
    for record in data:
        sensor_id = record["sensor_id"]
        temperature = record["temperature"]
        if sensor_id not in agg_results:
            agg_results[sensor_id] = {"sum_temp": 0.0, "count": 0}
        agg_results[sensor_id]["sum_temp"] += float(temperature)
        agg_results[sensor_id]["count"] += 1
    # Calculate average and prepare results
    results = []
    for sensor_id, agg in agg_results.items():
        avg_temp = agg["sum_temp"] / agg["count"] if agg["count"] > 0 else 0.0
        results.append((date_str, sensor_id, round(avg_temp, 2), agg["count"]))
    return results

def load_data(**kwargs):
    """Load transformed data into the daily_sensor_stats table in PostgreSQL."""
    ti = kwargs.get('ti')
    results = ti.xcom_pull(task_ids='transform')
    if not results:
        print("No data to load.")
        return "No data"
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    insert_query = """
        INSERT INTO daily_sensor_stats (date, sensor_id, avg_temperature, count_records)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (date, sensor_id)
        DO UPDATE SET avg_temperature = EXCLUDED.avg_temperature,
                      count_records = EXCLUDED.count_records;
    """
    # Convert date string to date object for insertion
    rows_to_insert = []
    for (date_str, sensor_id, avg_temp, count) in results:
        load_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        rows_to_insert.append((load_date, sensor_id, avg_temp, count))
    cur.executemany(insert_query, rows_to_insert)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(rows_to_insert)} rows into daily_sensor_stats.")
    return f"Loaded {len(rows_to_insert)} records."

# Default DAG arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "daily_iot_etl",
    description="Daily ETL pipeline for aggregating IoT sensor data",
    schedule_interval="@daily",
    start_date=datetime(2023, 1, 1),
    catchup=False,
    default_args=default_args
)

# Define the tasks
extract_task = PythonOperator(
    task_id="extract",
    python_callable=extract_data,
    dag=dag
)

transform_task = PythonOperator(
    task_id="transform",
    python_callable=transform_data,
    dag=dag
)

load_task = PythonOperator(
    task_id="load",
    python_callable=load_data,
    dag=dag
)

# Set task dependencies
extract_task >> transform_task >> load_task
