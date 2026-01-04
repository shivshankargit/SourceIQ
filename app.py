import streamlit as st
import os
import shutil
import time
import psycopg2
import zipfile
from git import Repo
import config

# Page Config: Centered layout looks more like a "Landing Page"
st.set_page_config(page_title="Codebase RAG", page_icon="🚀", layout="centered")

WATCH_DIR = config.WATCH_DIR

# --- HERO SECTION ---
import styles
styles.apply_custom_styles()

st.markdown('<h1 class="gradient-text">🚀 Chat with Codebase</h1>', unsafe_allow_html=True)
styles.glass_card(
    title="Stop searching. Start asking.",
    description="This tool turns any GitHub repository into an interactive knowledge base. Simply paste a URL or upload a ZIP to:",
    items=[
        "🧠 <strong>Understand</strong> complex logic instantly.",
        "🔍 <strong>Find</strong> exact file locations and references.",
        "⚡ <strong>Debug</strong> faster with context-aware answers."
    ]
)

st.divider()

# --- HELPER: CLEAN GITHUB URL ---
def normalize_github_url(url):
    """
    Cleans a GitHub URL to ensure it points to the root repository.
    """
    if "github.com" not in url:
        return url
        
    parts = url.rstrip("/").split("/")
    # Format: https:// [0] / [1] github.com [2] / user [3] / repo [4]
    if len(parts) >= 5:
        return "/".join(parts[:5])
    return url

# --- HELPER: RESET ENVIRONMENT ---
def reset_environment():
    """Clears the watch directory and database vectors."""
    # 1. Cleanup Files
    if os.path.exists(WATCH_DIR):
        def on_rm_error(func, path, exc_info):
            os.chmod(path, 0o777)
            func(path)
        shutil.rmtree(WATCH_DIR, onerror=on_rm_error)
    
    # 2. Clear Database
    # 2. Clear Database
    try:
        conn = psycopg2.connect(config.get_db_url())
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE code_vectors RESTART IDENTITY CASCADE;")
        conn.commit()
        conn.close()
        st.toast("🧹 Previous data cleared.")
    except Exception as e:
        # Stop execution if we can't clear the old data
        st.error(f"Failed to clear database: {e}")
        raise e

    # 3. Reset Session State
    if "messages" in st.session_state:
        st.session_state["messages"] = []
    if "trigger_query" in st.session_state:
        del st.session_state["trigger_query"]

# --- INPUT SECTION ---
st.subheader("Start your analysis")

tab1, tab2 = st.tabs(["🔗 GitHub Repository", "📂 Upload ZIP"])

# --- TAB 1: GITHUB ---
with tab1:
    repo_url_input = st.text_input("GitHub Repository URL", placeholder="https://github.com/netflix/conductor")
    
    if st.button("🚀 Analyze Repository", type="primary", use_container_width=True):
        if not repo_url_input:
            st.error("Please enter a valid GitHub URL.")
        else:
            repo_url = normalize_github_url(repo_url_input)
            
            with st.container(border=True):
                progress = st.progress(0)
                st.write("🔄 Preparing environment...")
                
                try:
                    reset_environment()
                    progress.progress(25)
                    
                    # Clone
                    st.write(f"⬇️ Cloning {repo_url}...")
                    os.makedirs(WATCH_DIR, exist_ok=True)
                    repo = Repo.clone_from(repo_url, WATCH_DIR)
                    progress.progress(50)
                    
                    # Store Metadata
                    st.session_state["current_repo_url"] = repo_url.replace(".git", "") 
                    st.session_state["current_branch"] = repo.active_branch.name
                    st.session_state["repo_loaded"] = True
                    
                    # Wait for Indexing
                    st.write("⚙️ Indexing code vectors...")
                    
                    # ... Polling Logic ...
                    max_retries = 30
                    retry_count = 0
                    vectors_found = False
                    
                    while retry_count < max_retries:
                        try:
                            conn = psycopg2.connect(config.get_db_url())
                            cur = conn.cursor()
                            cur.execute("SELECT count(*) FROM code_vectors")
                            count = cur.fetchone()[0]
                            conn.close()
                            if count > 0:
                                vectors_found = True
                                break
                        except:
                            pass
                        time.sleep(1)
                        retry_count += 1
                        progress.progress(50 + int((retry_count / max_retries) * 40))

                    if not vectors_found:
                        st.warning("⚠️ Indexing is slow, but proceeding.")
                    
                    progress.progress(100)
                    st.success("✅ Repository Ready!")
                    time.sleep(1)
                    st.switch_page("pages/overview.py")
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 2: ZIP UPLOAD ---
with tab2:
    uploaded_file = st.file_uploader("Upload a project ZIP file", type="zip")
    
    if uploaded_file is not None:
        if st.button("🚀 Analyze ZIP", type="primary", use_container_width=True):
            with st.container(border=True):
                progress = st.progress(0)
                st.write("🔄 Preparing environment...")
                
                try:
                    reset_environment()
                    progress.progress(25)
                    
                    # Extract Zip
                    st.write("📂 Extracting files...")
                    os.makedirs(WATCH_DIR, exist_ok=True)
                    
                    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                        zip_ref.extractall(WATCH_DIR)
                        
                    progress.progress(50)
                    
                    # Store Metadata
                    st.session_state["current_repo_url"] = "" # No URL for local files
                    st.session_state["current_branch"] = "main"
                    st.session_state["repo_loaded"] = True
                    
                    # Wait for Indexing
                    st.write("⚙️ Indexing code vectors...")
                    
                    # ... Polling Logic (Duplicated for now, could be helper) ...
                    max_retries = 30
                    retry_count = 0
                    vectors_found = False
                    
                    while retry_count < max_retries:
                        try:
                            conn = psycopg2.connect(config.get_db_url())
                            cur = conn.cursor()
                            cur.execute("SELECT count(*) FROM code_vectors")
                            count = cur.fetchone()[0]
                            conn.close()
                            if count > 0:
                                vectors_found = True
                                break
                        except:
                            pass
                        time.sleep(1)
                        retry_count += 1
                        progress.progress(50 + int((retry_count / max_retries) * 40))

                    progress.progress(100)
                    st.success("✅ Project Ready!")
                    time.sleep(1)
                    st.switch_page("pages/overview.py")
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("Powered by Gemini 2.5 Flash & pgvector")