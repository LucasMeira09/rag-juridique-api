from fastembed import TextEmbedding
from .db_connexion import RetrievalPipeline

class QuerySearch:
    # Handles semantic search queries against ChromaDB
    
    def __init__(self):
        self.model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.collection = RetrievalPipeline().collection
        self.categories_collection = RetrievalPipeline().categories_collection

    def get_category_names(self):
        data = self.categories_collection.get()
        return [meta["name"] for meta in data["metadatas"]]
        
    def query_search_db(self, query=""):
        # Search for relevant documents and return neighboring chunks
        if not query or query.strip() == "":
            return None
        
        # fastembed returns a generator, convert it to a list and get the first embedding
        query_embedding = list(self.model.embed([query]))[0]
        n_result = 3
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_result
        )
        
        final_result = []
        metadatas_dic = result["metadatas"][0]
        
        for i in range(n_result):
            metadata = metadatas_dic[i]
            idx = metadata["chunk_id"]
            
            neighbors = self.collection.get(
                where={
                    "chunk_id": {"$in": [idx-1, idx, idx+1]}
                }
            )
            
            doc_str = ""
            for doc in neighbors["documents"]:
                doc_str += str(doc)
            final_result.append(doc_str)
            
        return final_result, result