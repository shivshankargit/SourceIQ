import streamlit as st
import re
from collections import defaultdict
from rag_engine import generate_answer

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")

# --- SAFETY CHECK ---
if "repo_loaded" not in st.session_state:
    st.warning("⚠️ No repository loaded. Please go to the **Home** page first.")
    st.stop()

import styles
styles.apply_custom_styles()

st.markdown('<h1 class="gradient-text">💬 Chat with Codebase</h1>', unsafe_allow_html=True)

# --- HELPER: PARSE & GROUP CODE SNIPPETS ---
def parse_and_group_sources(source_text):
    """
    Parses raw source text from the backend and groups snippets by filename.
    Returns a dictionary of merged content for each file.
    """
    # Regex to find our specific header format
    pattern = r"--- FILE: (.*?) \(Match: (.*?)\) ---\n"
    parts = re.split(pattern, source_text)
    
    grouped_sources = defaultdict(list)
    
    # Iterate through regex matches (filename, type, content)
    for i in range(1, len(parts), 3):
        if i + 2 < len(parts):
            filename = parts[i].strip()
            match_type = parts[i+1].strip()
            content = parts[i+2].strip()
            
            grouped_sources[filename].append({
                "type": match_type,
                "content": content
            })

    # Merge logic: Combine snippets from the same file into one block
    final_sources = {}
    for filename, snippets in grouped_sources.items():
        # If any match was "semantic", we label the whole file as Semantic
        is_semantic = any("semantic" in s["type"].lower() for s in snippets)
        final_type = "Semantic" if is_semantic else "Keyword"
        
        # Join snippets with a clear visual separator
        merged_content = "\n\n# ... (more context) ...\n\n".join([s["content"] for s in snippets])
        
        final_sources[filename] = {
            "type": final_type,
            "content": merged_content
        }
        
    return final_sources

# --- HELPER: RENDER THE DEEPWIKI UI ---
def render_assistant_response(response_text, raw_sources):
    """
    Renders the Split View (Answer Left, Code Right)
    """
    # Create the Split Layout
    col1, col2 = st.columns([1, 1.2]) # Code column is slightly wider
    
    # LEFT COLUMN: The AI Answer
    with col1:
        st.markdown("### 🤖 Answer")
        with st.container(height=600):
            st.markdown(response_text)
            
            st.divider()
            st.caption("Suggested Actions:")
            
            # Modern "Pills" UI for suggestions
            action = st.pills(
                "Follow up:",
                ["Explain Concepts", "Generate Test", "Security Check"],
                selection_mode="single"
            )
            
            if action:
                query_map = {
                    "Explain Concepts": "Explain the core concepts and logic in the code above.",
                    "Generate Test": "Write a unit test for the code discussed above.",
                    "Security Check": "Are there any security vulnerabilities or bad practices here?"
                }
                st.session_state["trigger_query"] = query_map[action]
                st.rerun()
    
    # RIGHT COLUMN: The Referenced Code Cards
    with col2:
        st.markdown("### 📄 Context")
        with st.container(height=600):
            if raw_sources.strip():
                grouped_sources = parse_and_group_sources(raw_sources)
                
                # Get Repo Info for Links
                base_url = st.session_state.get("current_repo_url", "")
                branch = st.session_state.get("current_branch", "main")
                
                for filename, data in grouped_sources.items():
                    # Determine Icon
                    icon = "🧠" if "Semantic" in data['type'] else "🔍"
                    
                    # Create GitHub Link
                    if base_url:
                        # Format: https://github.com/user/repo/blob/main/path/file.py
                        # Fix for Windows paths: replace backslashes with forward slashes
                        safe_filename = filename.replace("\\", "/")
                        file_url = f"{base_url}/blob/{branch}/{safe_filename}"
                        header_link = f"[{filename}]({file_url})"
                    else:
                        header_link = filename
                    
                    # Render the Card
                    with st.container(border=True):
                        st.markdown(f"**{icon} {header_link}**")
                        
                        # Syntax Highlighting Logic
                        lang = "python" # Default
                        if filename.endswith(".js"): lang = "javascript"
                        if filename.endswith(".ts") or filename.endswith(".tsx"): lang = "typescript"
                        if filename.endswith(".html"): lang = "html"
                        if filename.endswith(".css"): lang = "css"
                        if filename.endswith(".md"): lang = "markdown"
                        if filename.endswith(".json"): lang = "json"
                        if filename.endswith(".java"): lang = "java"
                        
                        st.code(data['content'], language=lang)
                        st.caption(f"Match Source: {data['type']}")
            else:
                st.info("No specific code references found for this answer.")

# --- MAIN EXECUTION FLOW ---

# 1. Display Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 2. Handle Logic (Either Auto-Trigger OR User Input)
process_query = None

# Always render the chat input so it's visible
user_input = st.chat_input("Ask a question about the code...")

# A. Check for Auto-Trigger (from Overview Page)
if "trigger_query" in st.session_state:
    process_query = st.session_state.pop("trigger_query")
    # Note: We don't append to 'messages' here because Overview page already did it

# B. Check for Manual Input (Type in box)
elif user_input:
    process_query = user_input
    st.session_state.messages.append({"role": "user", "content": process_query})
    with st.chat_message("user"):
        st.markdown(process_query)

# 3. Generate & Display Response
if process_query:
    with st.chat_message("assistant"):
        with st.spinner("Analyzing codebase..."):
            # Call Backend with History
            answer, raw_sources = generate_answer(process_query, st.session_state.messages)
            
            # Render UI
            render_assistant_response(answer, raw_sources)
            
            # Save to History
            st.session_state.messages.append({"role": "assistant", "content": answer})