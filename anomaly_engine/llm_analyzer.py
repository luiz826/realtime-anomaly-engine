from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from . import config
from . import database # Import our new database module

# --- Initialize LangChain Components (globally) ---
llm = ChatOllama(model=config.OLLAMA_MODEL)
retriever = database.get_vector_store_retriever()

# 2. Define Prompt Template
template = """
You are a senior site reliability engineer (SRE) analyzing a production anomaly.
A high-level alert has already fired. Your job is to perform a root cause analysis.

Here is a sample of the raw error logs that triggered the alert:
---
{error_logs}
---

Here is historical context from past incidents in our runbook:
---
{context}
---

Based *only* on the logs and the historical context, provide a brief analysis.
Your analysis should be 3-4 sentences max.

1.  **Summary:** What is happening?
2.  **Hypothesis:** What is the probable root cause?
3.  **Recommendation:** What is the immediate next step?
"""
prompt = ChatPromptTemplate.from_template(template)

# 3. Define the RAG Chain
chain = (
    {"context": retriever, "error_logs": lambda x: x}
    | prompt
    | llm
    | StrOutputParser()
)

# --- Main Function ---
def get_llm_insight(raw_error_logs: list):
    """
    This is the main function called by Spark.
    It takes a list of raw log strings, runs the RAG chain, and saves the result.
    """
    print(f"🧠 LLM Analyzer triggered with {len(raw_error_logs)} logs.")
    
    # Format logs for the prompt
    log_sample = "\n".join(raw_error_logs[:10]) # Sample first 10
    
    # Run the RAG chain
    print("...querying RAG chain...")
    try:
        insight = chain.invoke(log_sample)
        print(f"💡 LLM Insight: {insight}")
        
        # Save the final insight
        database.save_llm_insight(insight)
        
    except Exception as e:
        print(f"❌ FAILED to get LLM insight: {e}")