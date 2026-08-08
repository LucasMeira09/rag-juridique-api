from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .reponse import Generation
from datetime import date
import time
import os

# uvicorn src.server.bridge:app --reload

app = FastAPI()

cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
if cors_origins_raw.strip() == "*":
    allow_origins = ["*"]
    allow_credentials = False
else:
    allow_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = Generation()

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Legal RAG API is running"}

class Query(BaseModel):
    query: str

@app.post("/search")
def search(data: Query):
    # Search endpoint that returns AI-generated answers based on document retrieval
    model_response, results = model.prompt_augmentation(data.query)

    if model_response == "rate" or model_response == "error":
        distance = results["distances"][0]
        relevance = max(0, (2 - distance[0]) / 2 * 100)
        
        metadatas = results["metadatas"][0]
        metadatas_topics = metadatas[0]
        
        payload = {
                "results": [
                    {
                        "id": 1,
                        "title": f"Résultat pour '{data.query}'",
                        "excerpt": "Please wait a few minutes before your next question. Thanks for your patience",
                        "source": metadatas_topics['source'],
                        "date": date.today().isoformat(),
                        "type": "Réponse IA",
                        "relevance": round(relevance),
                        "link": "#"  
                    }
                ]
            }
        return
    
    distance = results["distances"][0]
    relevance = max(0, (2 - distance[0]) / 2 * 100)
    
    metadatas = results["metadatas"][0]
    metadatas_topics = metadatas[0]
    
    payload = {
        "results": [
            {
                "id": 1,
                "title": f"Résultat pour '{data.query}'",
                "excerpt": model_response,
                "source": metadatas_topics['source'],
                "date": date.today().isoformat(),
                "type": "Réponse IA",
                "relevance": round(relevance),
                "link": "#"  
            }
        ]
    }
    
    return payload

@app.post("/admin/restart")
def trigger_restart():
    # Admin endpoint to restart the API container (called by pipeline after updates)
    import os
    import signal
    print("[ADMIN] Restart requested - shutting down to reload data...")
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "restarting"}