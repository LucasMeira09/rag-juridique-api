import chromadb 
import os
from pathlib import Path

# Chemin local vers la base ChromaDB
# Par défaut: dossier data/chroma_db à la racine du projet
_default_db_path = str(Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", _default_db_path)

class RetrievalPipeline:
    
    def __init__(self):
        db_path = os.path.abspath(CHROMA_DB_PATH)
        os.makedirs(db_path, exist_ok=True)
        
        print(f"[SERVER] Initialisation: Chargement de ChromaDB depuis {db_path}")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="law_text",
            metadata={"hnsw:space": "cosine"}
        )
        self.categories_collection = self.chroma_client.get_or_create_collection(
            name="categories",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"[SERVER] Collection chargée avec {self.collection.count()} documents")

    def cleanup(self):

        pass