import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from anomaly_engine import database

if __name__ == "__main__":
    database.setup_database_and_rag()