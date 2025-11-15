from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

from anomaly_engine import config
from anomaly_engine import streaming # <-- IMPORT STREAMING LOGIC

# --- 1. Initialize Spark Session ---
spark = SparkSession.builder \
    .appName(config.SPARK_APP_NAME) \
    .config("spark.sql.streaming.checkpointLocation", config.SPARK_CHECKPOINT_DIR) \
    .config("spark.jars", config.SPARK_JARS_PATH) \
    .config("spark.driver.extraJavaOptions", "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED") \
    .config("spark.executor.extraJavaOptions", "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR") # Hide INFO logs
print("Spark Session Initialized.")

# --- 2. Read from Kafka ---
raw_kafka_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", config.KAFKA_BROKER) \
    .option("subscribe", config.KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

# --- 3. Define Data Schema ---
schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("status_code", IntegerType(), True),
    StructField("error_message", StringType(), True)
])

# --- 4. Parse Kafka JSON ---
parsed_stream = raw_kafka_stream \
    .select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("timestamp", col("timestamp").cast(TimestampType()))

# --- 5. Process Metrics ---
metrics_stream = parsed_stream \
    .withWatermark("timestamp", "1 minute") \
    .groupBy(
        col("timestamp").alias("window_start"), # Tumbling window (uses foreachBatch)
        col("status_code")
    ) \
    .count() \
    .select(
        col("window_start"),
        col("status_code"),
        col("count").alias("event_count")
    )

# --- 6. Define Sinks (using our imported logic) ---

# SINK 1: Write metrics to TimescaleDB
metrics_query = metrics_stream.writeStream \
    .foreachBatch(streaming.write_metrics_to_db) \
    .outputMode("update") \
    .trigger(processingTime='30 seconds') \
    .start()

# SINK 2: Analyze anomalies (raw stream)
anomaly_query = parsed_stream.writeStream \
    .foreachBatch(streaming.analyze_anomalies) \
    .outputMode("append") \
    .trigger(processingTime='30 seconds') \
    .start()

# --- 7. Start Streams ---
print(f"Spark Streaming queries started. Listening to Kafka topic '{config.KAFKA_TOPIC}'...")
print("(Make sure run_producer.py is running in another terminal)")
spark.streams.awaitAnyTermination()