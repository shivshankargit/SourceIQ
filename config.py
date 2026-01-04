import os
import streamlit as st

# Default to local postgres if not set
DEFAULT_DB_URL = "postgresql://user:password@localhost:5432/vectordb"

def get_db_url():
    # Priority: Env Var (Docker) > Local Default
    return os.environ.get("COCOINDEX_DATABASE_URL", "postgresql://user:password@localhost:5432/vectordb")

def get_google_api_key():
    # Try env var, then search specifically for Streamlit secrets if available, else fallback
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        # Fallback placeholder - User should start using .env or environment variables
        api_key = "" 
    return api_key

# Constants
WATCH_DIR = os.path.abspath("./my_project_code")
