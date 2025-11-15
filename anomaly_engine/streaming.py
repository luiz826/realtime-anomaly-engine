from . import config
from . import database
from .llm_analyzer import get_llm_insight # Import our analyzer

def write_metrics_to_db(batch_df, epoch_id):
    """Writes aggregated metrics to our Postgres/TimescaleDB."""
    print(f"--- Writing Metrics Batch {epoch_id} ---")
    try:
        # Write the batch to the 'metrics' table
        batch_df.write \
            .jdbc(url=config.JDBC_URL, table="metrics", mode="append", properties=config.DB_PROPERTIES)
        
        # HACK: Ensure hypertable exists. Only runs once.
        # A better solution would be in an init script, but this works.
        conn = database.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                window_start TIMESTAMPTZ,
                status_code INTEGER,
                event_count BIGINT
            );
            SELECT create_hypertable('metrics', 'window_start', if_not_exists => TRUE);
        """)
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        # Catch errors (e.g., DB not ready)
        print(f"Error writing metrics to DB: {e}")

def analyze_anomalies(batch_df, epoch_id):
    """
    The "smoke alarm." Checks a batch for anomalies and triggers the LLM.
    """
    print(f"--- Analyzing Anomaly Batch {epoch_id} ---")
    
    # Collect all data to the driver (OK for micro-batches)
    batch_data = batch_df.collect()
    total_count = len(batch_data)
    
    if total_count == 0:
        return # Empty batch

    # 1. The "Smoke Alarm": Calculate error rate
    error_logs = [
        row.error_message for row in batch_data 
        if row.status_code == 500 and row.error_message is not None
    ]
    error_count = len(error_logs)
    error_rate = error_count / total_count
    
    print(f"Batch Error Rate: {error_rate:.2%} ({error_count} errors)")

    # 2. The "Trigger"
    if error_rate > config.ANOMALY_ERROR_RATE_THRESHOLD and error_count > config.ANOMALY_MIN_ERROR_COUNT:
        print(f"🚨 ANOMALY DETECTED! Rate: {error_rate:.2%}")
        
        # 3. The "Firefighter": Call LLM
        # Get distinct error messages
        distinct_errors = list(set(error_logs))
        get_llm_insight(distinct_errors)