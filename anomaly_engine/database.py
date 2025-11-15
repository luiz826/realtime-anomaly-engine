import psycopg2
from langchain_community.document_loaders import TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config # Import from our config file

def get_db_connection():
    """Returns a standard psycopg2 connection."""
    return psycopg2.connect(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_NAME
    )

def setup_database_and_rag():
    """One-time setup to create vector extension and ingest RAG data."""
    print("--- Setting up Database and RAG ---")
    
    # 1. Enable pgvector and drop old tables if they exist
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Drop old langchain tables (they use old schema)
        print("Dropping old vector tables if they exist...")
        cur.execute("DROP TABLE IF EXISTS langchain_pg_embedding CASCADE;")
        cur.execute("DROP TABLE IF EXISTS langchain_pg_collection CASCADE;")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ pgvector extension enabled and old tables dropped.")
    except Exception as e:
        print(f"❌ Error enabling pgvector: {e}")
        return

    # 2. Load, split, and ingest RAG documents
    try:
        loader = TextLoader(config.RAG_DATA_PATH)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        print(f"Split runbook into {len(docs)} chunks.")

        embeddings = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
        
        print("Ingesting documents into PGVector...")
        PGVector.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_name=config.VECTOR_COLLECTION_NAME,
            connection=config.DB_URL,
            pre_delete_collection=True, # Clear old data
        )
        print("✅ Vector Database setup complete!")
    except Exception as e:
        print(f"❌ Error setting up RAG: {e}")

def get_vector_store_retriever():
    """Initializes and returns a RAG retriever."""
    embeddings = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
    vector_store = PGVector(
        collection_name=config.VECTOR_COLLECTION_NAME,
        connection=config.DB_URL,
        embeddings=embeddings,
        use_jsonb=True,  # Use JSONB for better performance
    )
    # Get top 2 similar results
    return vector_store.as_retriever(search_kwargs={"k": 2})

def save_llm_insight(insight_text: str):
    """Saves the LLM's final analysis to the 'llm_alerts' table."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Ensure the table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS llm_alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                insight_text TEXT
            );
        """)
        
        sql = "INSERT INTO llm_alerts (insight_text) VALUES (%s)"
        cur.execute(sql, (insight_text,))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Saved insight to DB.")
    except Exception as e:
        print(f"❌ FAILED to save insight to DB: {e}")