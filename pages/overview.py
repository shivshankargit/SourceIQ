import streamlit as st
import os
from collections import Counter
from rag_engine import generate_summary # Import the new function

st.set_page_config(page_title="Repo Overview", layout="wide")
WATCH_DIR = "./my_project_code"

if "repo_loaded" not in st.session_state:
    st.warning("⚠️ No repository loaded. Please go to the **Home** page first.")
    st.stop()

# --- HELPER: GET FILE STATS ---
def get_repo_details(directory):
    total_files = 0
    extensions = []
    file_tree = []
    
    for root, _, files in os.walk(directory):
        if ".git" in root: continue
        level = root.replace(directory, '').count(os.sep)
        if level < 2: # Only get top 2 levels for context
            indent = ' ' * 4 * (level)
            file_tree.append(f"{indent}{os.path.basename(root)}/")
            for f in files[:5]: # Limit files per folder for context
                file_tree.append(f"{indent}    {f}")
                
        for file in files:
            total_files += 1
            ext = os.path.splitext(file)[1]
            if ext: extensions.append(ext)
            
    return total_files, Counter(extensions), "\n".join(file_tree)

# --- LOAD DATA (Cached to prevent re-running LLM on every click) ---
# --- UI LAYOUT ---
import styles
styles.apply_custom_styles()

st.markdown('<h1 class="gradient-text">📊 Smart Overview</h1>', unsafe_allow_html=True)

# --- LOAD DATA ---
# (Cached to prevent re-running LLM on every click)
# We pass 'repo_url' as an argument so Streamlit invalidates the cache when the repo changes
@st.cache_data(show_spinner=False)
def get_ai_analysis(repo_url):
    files_count, ext_counts, file_tree = get_repo_details(WATCH_DIR)
    
    # Read README
    readme_text = ""
    readme_path = os.path.join(WATCH_DIR, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
            readme_text = f.read()
            
    # Generate Summary
    summary = generate_summary(readme_text, file_tree)
    return summary, files_count, ext_counts

# Get the current repo URL to use as a cache key
current_repo_url = st.session_state.get("current_repo_url", "unknown")

with st.spinner("🤖 AI is analyzing the repository..."):
    summary_text, total_files, tech_stack = get_ai_analysis(current_repo_url)

# 1. AI Summary Section
styles.glass_card(summary_text)

# --- VISUALIZATION SECTION ---
st.divider()

st.subheader("🗺️ Codebase Map")

def build_graph(directory, max_depth=2):
    """
    Builds a DOT format string for Graphviz.
    """
    dot = [
        'digraph G {',
        'bgcolor="transparent";',
        'rankdir=TB;', # Top to Bottom flow is usually easier to read
        'splines=ortho;', # Orthogonal lines look cleaner
        'nodesep=0.6;',
        'ranksep=1.0;',
        'node [shape=box, style="filled,rounded", fontname="Inter", fontsize=12, margin="0.2,0.1"];',
        'edge [penwidth=1.5, color="#636e72"];'
    ]
    
    # Root node
    root_name = os.path.basename(directory)
    dot.append(f'"{root_name}" [label="{root_name}", fillcolor="#6C5CE7", fontcolor="white", penwidth=0];')
    
    for root, dirs, files in os.walk(directory):
        if ".git" in root: continue
        
        # Calculate depth
        rel_path = os.path.relpath(root, directory)
        current_depth = 0 if rel_path == "." else rel_path.count(os.sep) + 1
        
        if current_depth >= max_depth:
            continue
            
        parent_node = os.path.basename(root)
        if rel_path == ".": parent_node = root_name
        
        # Add Folders
        for d in dirs:
            if d.startswith("."): continue
            # Sleek Folder Node
            dot.append(f'"{d}" [label="{d}", fillcolor="#2d3436", fontcolor="white", color="#6C5CE7", penwidth=2];')
            dot.append(f'"{parent_node}" -> "{d}";')
            
        # Add Files (limit to avoid noise)
        for f in files[:8]: 
            # Minimalist File Node
            color = "#b2bec3" # Default Grey
            if f.endswith(".py"): color = "#fdcb6e" # Yellow
            elif f.endswith(".js") or f.endswith(".ts"): color = "#74b9ff" # Blue
            elif f.endswith(".md"): color = "#55efc4" # Green
            elif f.endswith(".css"): color = "#a29bfe" # Purple
            
            # White background with colored text/border
            dot.append(f'"{f}" [label="{f}", style="rounded,filled", fillcolor="#1E1E26",fontcolor="{color}", color="{color}", penwidth=1];')
            dot.append(f'"{parent_node}" -> "{f}";')
            
    dot.append('}')
    return "\n".join(dot)

graph_dot = build_graph(WATCH_DIR)

# Render Graph safely
try:
    st.graphviz_chart(graph_dot)
except Exception as e:
    st.info("Visual map requires Graphviz. Showing file tree instead.")
    st.text(file_tree if 'file_tree' in locals() else "No tree data.")

# 3. "Ask from Anywhere" Section

# 3. "Ask from Anywhere" Section
st.subheader("💬 Start Investigating")
st.write("Have a question about this overview? Ask it right here.")

# This input sends the user to the Chat page
quick_prompt = st.chat_input("Ex: Where is the main entry point defined?")

if quick_prompt:
    # 1. Save the question to session state so Chat page can see it
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    st.session_state["messages"].append({"role": "user", "content": quick_prompt})
    st.session_state["trigger_query"] = quick_prompt # Flag to trigger generation
    
    # 2. Redirect
    st.switch_page("pages/chat.py")