import streamlit as st



def apply_custom_styles():

    st.markdown("""

        <style>

            /* Import Google Fonts: Outfit (Headings) and Inter (Body) */

            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@500;700&display=swap');



            /* Global Font Updates */

            html, body, [class*="css"] {

                font-family: 'Inter', sans-serif;

            }

           

            h1, h2, h3 {

                font-family: 'Outfit', sans-serif !important;

                font-weight: 700 !important;

            }



            /* Glassmorphism Cards */

            .glass-card {

                background: rgba(255, 255, 255, 0.05);

                backdrop-filter: blur(10px);

                -webkit-backdrop-filter: blur(10px);

                border: 1px solid rgba(255, 255, 255, 0.1);

                border-radius: 16px;

                padding: 24px;

                margin-bottom: 20px;

                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

            }

           

            /* Gradient Text for Titles */

            .gradient-text {

                background: linear-gradient(45deg, #6C5CE7, #a29bfe);

                -webkit-background-clip: text;

                -webkit-text-fill-color: transparent;

                font-weight: bold;

            }



            /* Custom Button Styling */

            div.stButton > button {

                background: linear-gradient(45deg, #6C5CE7, #8e44ad);

                color: white;

                border: none;

                border-radius: 8px;

                padding: 0.5rem 1rem;

                font-weight: 600;

                transition: all 0.3s ease;

            }

            div.stButton > button:hover {

                transform: translateY(-2px);

                box-shadow: 0 5px 15px rgba(108, 92, 231, 0.4);

            }



            /* Input Fields */

            .stTextInput > div > div > input {

                background-color: #1E1E26;

                border: 1px solid #6C5CE7;

                border-radius: 8px;

                color: #FAFAFA;

            }



            /* Remove default top padding */

            .block-container {

                padding-top: 2rem;

            }

           

            /* Chat Message Bubbles */

            .stChatMessage {

                background-color: transparent;

                border: none;

            }

           

            /* Code Block Styling */

            code {

                font-family: 'JetBrains Mono', monospace !important;

            }



        </style>

    """, unsafe_allow_html=True)

def glass_card(content=None, title=None, description=None, items=None):
    """
    Renders a glassmorphism card. 
    Can be called with a single string (content) OR specific named arguments (title, description, items).
    """
    
    # 1. Handle "Old Style" calls (just passing a string)
    if content and not title and not description:
        # If it's a simple markdown string, just render it
        html_content = f"""
        <div class="glass-card">
            {content}
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
        return

    # 2. Handle "New Style" calls (title, description, items)
    inner_html = ""
    
    if title:
        inner_html += f"<h3>{title}</h3>"
        
    if description:
        inner_html += f"<p>{description}</p>"
        
    if items:
        inner_html += "<ul>"
        for item in items:
            inner_html += f"<li>{item}</li>"
        inner_html += "</ul>"
        
    # Wrap in the glass card div
    final_html = f"""
    <div class="glass-card">
        {inner_html}
    </div>
    """
    st.markdown(final_html, unsafe_allow_html=True)