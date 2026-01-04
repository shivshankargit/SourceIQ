import os
import psycopg2
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import config
import time
import random

# --- CONFIGURATION ---
api_key = config.get_google_api_key()
genai.configure(api_key=api_key)

# 2. MODEL: Use standard model
model = genai.GenerativeModel('gemini-2.5-flash')

# --- HELPER: RETRY WITH BACKOFF ---
def retry_with_backoff(func):
    """
    Simple decorator to retry functions on 429 errors.
    """
    def wrapper(*args, **kwargs):
        max_retries = 5
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check for 429 explicitly in the error message
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    if attempt == max_retries - 1:
                        raise e # Give up after last try
                        
                    # Exponential Backoff + Jitter: 2s, 4s, 8s...
                    sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"⚠️ Quota hit. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    raise e # Don't retry other errors (like 401 Auth)
    return wrapper

embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_db_connection():
    return psycopg2.connect(config.get_db_url())

def retrieve_context(query):
    # Connect to Postgres using config
    conn = get_db_connection()
    cur = conn.cursor()
    
    # ---------------------------------------------------------
    # STRATEGY A: SEMANTIC SEARCH (Vector)
    # ---------------------------------------------------------
    query_vector = embedder.encode(query).tolist()
    sql_vector = """
    SELECT filename, text, 1 - (embedding <=> %s::vector) as score, 'semantic' as source
    FROM code_vectors
    ORDER BY score DESC LIMIT 4;
    """
    cur.execute(sql_vector, (query_vector,))
    semantic_results = cur.fetchall()

    # ---------------------------------------------------------
    # STRATEGY B: KEYWORD SEARCH (Exact Match)
    # ---------------------------------------------------------
    # Filter for significant words (len > 3) to avoid "the", "and", etc.
    search_terms = [word for word in query.split() if len(word) > 3]
    keyword_results = []
    
    if search_terms:
        # Create a dynamic SQL query: text ILIKE '%term1%' OR text ILIKE '%term2%'
        conditions = " OR ".join(["text ILIKE %s" for _ in search_terms])
        sql_keyword = f"""
        SELECT filename, text, 0.9 as score, 'keyword' as source
        FROM code_vectors
        WHERE {conditions}
        LIMIT 3;
        """
        # Add % wildcards for partial matching
        params = [f"%{term}%" for term in search_terms]
        cur.execute(sql_keyword, params)
        keyword_results = cur.fetchall()
    
    conn.close()
    
    # ---------------------------------------------------------
    # MERGE & DEDUPLICATE
    # ---------------------------------------------------------
    seen_texts = set()
    final_results = []
    
    # Add Semantic Results First (High priority)
    for res in semantic_results:
        filename, text, score, source = res
        if text not in seen_texts:
            final_results.append(res)
            seen_texts.add(text)
            
    # Add Keyword Results (Only if new)
    for res in keyword_results:
        filename, text, score, source = res
        if text not in seen_texts:
            final_results.append(res)
            seen_texts.add(text)
    
    # Format for LLM
    context_str = ""
    for filename, text, score, source in final_results:
        context_str += f"\n--- FILE: {filename} (Match: {source}) ---\n{text}\n"
    
    return context_str

def generate_summary(readme_text, file_structure_text):
    """
    Generates a structured overview of the repository using the LLM.
    """
    prompt = f"""
    You are a Senior Technical Writer. Analyze this GitHub repository based on its README and file structure.
    
    README CONTENT:
    {readme_text[:5000]} (truncated)
    
    FILE STRUCTURE TOP LEVELS:
    {file_structure_text}
    
    OUTPUT REQUIREMENTS:
    1. **Project Name & One-Liner**: A catchy title and single sentence description.
    2. **Core Functionality**: 3-4 bullet points explaining what the project actually *does* (not just how to install it).
    3. **Key Technologies**: List the main languages/frameworks detected.
    4. **Target Audience**: Who is this for? (e.g., Data Scientists, Web Devs).
    
    Format the output in clean HTML (using <h3> for the title, <ul>/<li> for lists, <p>, <strong>). Do NOT use code blocks or markdown formatting.
    """
    
    @retry_with_backoff
    def run_llm():
        response = model.generate_content(prompt)
        return response.text

    try:
        return run_llm()
    except Exception as e:
        return f"Could not generate summary (Quota Exceeded): {e}"

def generate_answer(query, chat_history=[]):
    context = retrieve_context(query)
    
    if not context.strip():
        return "I couldn't find any relevant code in the repository. Try rephrasing or checking if the code is indexed.", ""

    # Format history for the prompt
    history_str = ""
    if chat_history:
        history_str = "\nPREVIOUS CONVERSATION:\n"
        for msg in chat_history[-6:]: # Keep last 3 turns (User + AI)
            role = "User" if msg["role"] == "user" else "Assistant"
            history_str += f"{role}: {msg['content']}\n"

    prompt = f"""
    You are a concise assistant for answering questions about the currently loaded GitHub repository.
    Always ground answers in repository content.
    
    {history_str}
    
    Use the 'retrieve' tool first with a targeted query to fetch relevant context before answering.
    If retrieved context is insufficient or unrelated, ask a brief clarifying question.
    Prefer facts found in the repo; do not guess. If information is missing, say so and suggest next steps.
    Cite specific files and short snippets when helpful; keep snippets minimal.
    For run/build/test/setup questions, check README/docs/manifests/config files and provide exact commands and file locations.
    When explaining code, mention function/class names, responsibilities, parameters, and data flow.
    Keep responses short and actionable.
    
    CONTEXT:
    {context}
    
    QUESTION: {query}
    
    GUIDELINES:
    1. Use the provided CONTEXT to answer.
    2. If the answer involves specific code, cite the Filename provided in the context.
    3. Keep responses short and actionable.
    4. If the context is empty or irrelevant, say "I don't know based on the current code."
    """
    
    @retry_with_backoff
    def run_llm():
        response = model.generate_content(prompt)
        return response.text, context

    try:
        return run_llm()
    except Exception as e:
        return f"Error connecting to Gemini (Quota Exceeded): {e}", context