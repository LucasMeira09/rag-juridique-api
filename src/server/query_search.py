from fastembed import TextEmbedding
from .db_connexion import RetrievalPipeline
import unicodedata
import re

# Stop words français courants à supprimer pour améliorer la précision de la recherche
FRENCH_STOP_WORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d",
    "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
    "notre", "nos", "votre", "vos", "leur", "leurs",
    "ce", "cet", "cette", "ces",
    "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "on",
    "me", "te", "se", "lui",
    "et", "ou", "mais", "donc", "car", "ni", "que", "qu",
    "en", "au", "aux", "par", "pour", "avec", "dans", "sur", "sous",
    "est", "sont", "a", "ai", "as", "ont", "suis", "es", "soit",
    "ne", "pas", "plus", "rien", "jamais",
    "qui", "quoi", "dont", "y",
    "si", "bien", "tres", "trop", "peu", "aussi",
    "tout", "toute", "tous", "toutes",
    "autre", "autres", "meme", "memes",
    "quel", "quelle", "quels", "quelles",
    "comment", "combien", "quand", "pourquoi",
    "faire", "fait", "faut",
    "etre", "avoir", "peut", "doit",
    "l", "c", "s", "n", "j", "m", "t",
}

# Seuil de distance max : au-delà, le résultat est considéré comme non pertinent
MAX_DISTANCE_THRESHOLD = 1.2

class QuerySearch:
    # Handles semantic search queries against ChromaDB
    
    def __init__(self):
        self.model = TextEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            threads=1,
            providers=["CPUExecutionProvider"]
        )
        self.collection = RetrievalPipeline().collection
        self.categories_collection = RetrievalPipeline().categories_collection

    def get_category_names(self):
        data = self.categories_collection.get()
        return [meta["name"] for meta in data["metadatas"]]

    def _normalize_query(self, query):
        """Normalise la requête pour améliorer la précision de la recherche sémantique.
        
        1. Mise en minuscules
        2. Suppression des accents
        3. Suppression des stop words français
        4. Nettoyage des espaces multiples
        """
        # Minuscules
        text = query.lower().strip()
        # Suppression des accents
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        # Tokenisation simple et suppression des stop words
        words = re.split(r"['\s\-]+", text)
        filtered = [w for w in words if w and w not in FRENCH_STOP_WORDS]
        # Reconstruction
        normalized = " ".join(filtered)
        # Si tout a été filtré, on garde la requête originale nettoyée
        return normalized if normalized.strip() else text
        
    def query_search_db(self, query=""):
        # Search for relevant documents and return neighboring chunks
        if not query or not str(query).strip():
            return [], None
        
        count = self.collection.count()
        if count == 0:
            return [], None
        
        # Normalise la requête pour réduire le bruit (articles, pronoms, accents)
        normalized_query = self._normalize_query(str(query))
        
        # fastembed returns a generator, convert it to a list and get the first embedding
        query_embedding = list(self.model.embed([normalized_query]))[0]
        n_result = min(5, count)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_result
        )
        
        final_result = []
        metadatas_dic = result["metadatas"][0] if result and result.get("metadatas") else []
        distances = result["distances"][0] if result and result.get("distances") else []
        
        for i in range(min(n_result, len(metadatas_dic))):
            # Filtre les résultats dont la distance dépasse le seuil de pertinence
            if i < len(distances) and distances[i] > MAX_DISTANCE_THRESHOLD:
                continue
                
            metadata = metadatas_dic[i]
            idx = metadata.get("chunk_id", 0)
            
            neighbors = self.collection.get(
                where={
                    "chunk_id": {"$in": [idx-1, idx, idx+1]}
                }
            )
            
            doc_str = ""
            if neighbors and neighbors.get("documents"):
                for doc in neighbors["documents"]:
                    doc_str += str(doc)
            final_result.append(doc_str)
            
        return final_result, result