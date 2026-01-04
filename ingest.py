import os
import cocoindex
from datetime import timedelta
from cocoindex.sources import LocalFile
from cocoindex.targets import Postgres
from cocoindex.functions import SplitRecursively, SentenceTransformerEmbed
from cocoindex import FlowLiveUpdater
import config

# --- CONFIGURATION FIX ---
# CocoIndex requires the connection to be set via this environment variable.
# It uses this for both storing the vectors AND tracking the pipeline state.
os.environ["COCOINDEX_DATABASE_URL"] = config.get_db_url()

# Helper function to detect language based on file extension
@cocoindex.op.function()
def get_language(filename: str) -> str:
    ext = os.path.splitext(filename)[1]
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".md": "markdown"
    }
    return mapping.get(ext, "text")

@cocoindex.flow_def(name="CodebaseRag")
def code_indexing_flow(flow_builder, data_scope):
    
    # 1. SOURCE: Watch your code folder
    data_scope["files"] = flow_builder.add_source(
        LocalFile(
            path=config.WATCH_DIR, 
            included_patterns=["*.py", "*.js", "*.md"]
        ),
        refresh_interval=timedelta(seconds=10) 
    )

    # 2. COLLECTOR: Create a collection point
    vector_store = data_scope.add_collector()

    # 3. TRANSFORM: Parse, Chunk, and Embed
    with data_scope["files"].row() as file:
        file["lang"] = file["filename"].transform(get_language)
        
        file["chunks"] = file["content"].transform(
            SplitRecursively(), 
            language=file["lang"], 
            chunk_size=512, 
            chunk_overlap=50
        )

        with file["chunks"].row() as chunk:
            chunk["embedding"] = chunk["text"].transform(
                SentenceTransformerEmbed(model="sentence-transformers/all-MiniLM-L6-v2")
            )
            
            vector_store.collect(
                filename=file["filename"],
                location=chunk["location"],
                text=chunk["text"],
                embedding=chunk["embedding"]
            )

    # 4. EXPORT: Save to Postgres
    # FIX: No connection args here! It uses COCOINDEX_DATABASE_URL automatically.
    vector_store.export(
        "code_embeddings", 
        Postgres(table_name="code_vectors"), 
        primary_key_fields=["filename", "location"],
        vector_indexes=[
            cocoindex.VectorIndexDef(
                field_name="embedding", 
                metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY
            )
        ]
    )

if __name__ == "__main__":
    print("🛠️  Setting up database tables...")
    # This creates the tables using the COCOINDEX_DATABASE_URL defined at the top
    code_indexing_flow.setup()
    
    print("🚀 Starting Live Codebase Indexer... (Press Ctrl+C to stop)")
    updater = FlowLiveUpdater(code_indexing_flow)
    
    try:
        updater.start()
        updater.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping indexer...")
        updater.abort()