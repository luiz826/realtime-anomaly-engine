import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set JAVA_HOME if specified in .env
if os.getenv("JAVA_HOME"):
    os.environ["JAVA_HOME"] = os.getenv("JAVA_HOME")
    os.environ["PATH"] = f"{os.getenv('JAVA_HOME')}/bin:{os.environ.get('PATH', '')}"

# --- Database Config ---
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
DB_NAME = os.getenv("POSTGRES_DB", "anomaly_db")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Connection string for LangChain (psycopg2)
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connection string for Spark (JDBC)
JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
DB_PROPERTIES = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "driver": "org.postgresql.Driver"
}

# --- Kafka Config ---
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "e-commerce-logs")

# --- LLM & RAG Config ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "llama3")
VECTOR_COLLECTION_NAME = os.getenv("VECTOR_COLLECTION_NAME", "incident_runbooks")
RAG_DATA_PATH = os.getenv("RAG_DATA_PATH", "./data/runbook.md")

# --- Spark Config ---
SPARK_APP_NAME = os.getenv("SPARK_APP_NAME", "AnomalyDetectionEngine")
SPARK_CHECKPOINT_DIR = os.getenv("SPARK_CHECKPOINT_DIR", "/tmp/spark-checkpoints")
SPARK_JARS_PATH = os.getenv("SPARK_JARS_PATH", "./jars/*")

# --- Logic Config ---
ANOMALY_ERROR_RATE_THRESHOLD = float(os.getenv("ANOMALY_ERROR_RATE_THRESHOLD", 0.20))
ANOMALY_MIN_ERROR_COUNT = int(os.getenv("ANOMALY_MIN_ERROR_COUNT", 5))