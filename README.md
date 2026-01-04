# 🚀 SourceIQ: Chat with your Code

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-orange)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-purple)

**sourceIQ** is an advanced Retrieval-Augmented Generation (RAG) tool designed to bridge the gap between complex software repositories and human understanding. It turns any GitHub repository or uploaded ZIP file into an interactive knowledge base, allowing developers to "chat" with the code logic, find precise references, and debug faster.

---

## 🌟 Key Features

*   **🔍 Hybrid Search Engine:** Combines **Semantic Search** (Vector Embeddings) with **Keyword Search** (SQL) to find both conceptual matches and exact function names.
*   **🧠 AI-Powered Insights:** Uses **Google Gemini 2.5 Flash** to explain logic, summarize files, and suggest fixes.
*   **📊 Smart Overview:** Automatically detects tech stacks, counts lines of code, and visualizes dependency graphs.
*   **⚡ Live Indexing Pipeline:** Powered by `CocoIndex` to actively watch and re-index files as they change (if running locally).
*   **🔒 Secure & Local:** Code vectors are stored in a local PostgreSQL/pgvector instance.

---

## 📸 Screenshots

| Landing Page | Chat Interface |
|:---:|:---:|
|<img width="1858" height="922" alt="landing_page" src="https://github.com/user-attachments/assets/ce2cb426-52d5-44e5-91a0-698494371f2f" />|<img width="1857" height="916" alt="chat" src="https://github.com/user-attachments/assets/8ddbcc9f-976a-4526-9448-a59eb86e8cde" />

---

## 🏗️ Architecture

The project is built on a modern, scalable stack:

1.  **Ingestion Agent (`ingest.py`):** A background process that watches files, splits them into recursive chunks, and computes embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
2.  **Vector Database:** **PostgreSQL** with the `pgvector` extension stores the code embeddings.
3.  **RAG Engine (`rag_engine.py`):** Handles the retrieval logic and connection to the Google Gemini API.
4.  **Frontend (`app.py`):** A sleek **Streamlit** interface with Glassmorphism UI elements.

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project running on your local machine.

### Prerequisites

*   **Docker & Docker Compose** (Recommended method)
*   **Google Gemini API Key** (Get one [here](https://aistudio.google.com/))

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/shivshankargit/SourceIQ.git
    cd SourceIQ
    ```

2.  **Configure Environment:**
    Copy the example environment file and add your API key.
    ```bash
    cp .env.example .env
    ```
    *Open `.env` and set `GOOGLE_API_KEY=your_api_key_here`*

3.  **Run with Docker:**
    Build and start the services.
    ```bash
    docker-compose up --build
    ```

4.  **Access the App:**
    Open your browser and navigate to:
    ```
    http://localhost:8501
    ```

---

## 📖 Usage Guide

### 1. Load a Repository
*   **GitHub URL:** Paste the full URL of any public GitHub repository (e.g., `https://github.com/netflix/conductor`).
*   **ZIP Upload:** Drag and drop a project ZIP file.
*   *Click "Analyze" and wait for the "Repository Ready" signal.*

### 2. View the Overview
*   Check the generated **AI Summary** to understand what the project does.
*   Review the file tree and language breakdown.

### 3. Chat with the Code
*   Ask questions like:
    *   *"Where is the authentication logic handled?"*
    *   *"How does the `ingest.py` pipeline work?"*
    *   *"Write a unit test for the `normalize_url` function."*
*   The AI will provide an answer on the left and show **cited code snippets** on the right.

---

## 🛠️ Development

If you want to run it without Docker (for debugging):

1.  **Install System Deps:** Ensure PostgreSQL is installed and running locally with `pgvector`.
2.  **Install Python Deps:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the App:**
    ```bash
    streamlit run app.py
    ```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  <small>Powered by Streamlit & Google Gemini</small>
</p>

