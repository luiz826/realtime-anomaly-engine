import json
import time
import random
from faker import Faker
from kafka import KafkaProducer
from datetime import datetime
from anomaly_engine import config # <-- IMPORT CONFIG

# Initialize Kafka Producer
try:
    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BROKER, # <-- From config
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
except Exception as e:
    print(f"❌ FAILED to connect to Kafka at {config.KAFKA_BROKER}: {e}")
    exit(1)

# Kafka topic
TOPIC_NAME = config.KAFKA_TOPIC # <-- From config

# (The rest of the producer.py logic is identical)
# ... (paste the get_log_message and simulate_anomaly_burst functions here) ...

# Error message templates
ERROR_MESSAGES = [
    "Connection Timeout: Upstream service 'Bank XYZ' not responding.",
    "Database Error: Failed to write payment record.",
    "SKU out of stock: Item 12345.",
    "Invalid API Key: 'cart-service' auth failed."
]

def get_log_message():
    """Generates a single log message."""
    fake = Faker()
    now = datetime.now().isoformat()
    
    # 95% chance of a "normal" event
    if random.random() < 0.95:
        status_code = random.choice([200, 201, 302])
        error = None
        event_type = random.choice(['view_item', 'add_to_cart', 'checkout_page'])
    else:
        # 5% chance of an "anomaly" event
        status_code = 500
        error = random.choice(ERROR_MESSAGES)
        event_type = 'payment_status'
        
    return {
        "timestamp": now,
        "user_id": fake.uuid4(),
        "event_type": event_type,
        "status_code": status_code,
        "error_message": error
    }

def simulate_anomaly_burst(duration_seconds=30, rate_per_second=10):
    """Simulates a sudden burst of a specific error."""
    print(f"--- SIMULATING ANOMALY BURST for {duration_seconds}s ---")
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        log = get_log_message()
        # Force the anomaly
        log['status_code'] = 500
        log['error_message'] = "Connection Timeout: Upstream service 'Bank XYZ' not responding."
        log['event_type'] = 'payment_status'
        
        producer.send(TOPIC_NAME, log)
        time.sleep(1.0 / rate_per_second)
    print("--- Anomaly burst finished ---")

print(f"Starting data producer for topic '{TOPIC_NAME}'...")
try:
    while True:
        for _ in range(random.randint(1, 5)):
            log_data = get_log_message()
            producer.send(TOPIC_NAME, log_data)

        producer.flush()
        
        if random.random() < 0.01:
            simulate_anomaly_burst()

        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping producer.")
finally:
    producer.close()