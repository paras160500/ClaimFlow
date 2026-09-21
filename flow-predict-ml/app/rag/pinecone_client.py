"""
    upserting the data to pinecone
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os 
from dotenv import load_dotenv
load_dotenv()
from typing import Any, Dict, List, Tuple
from pinecone import Pinecone 
from pinecone import ServerlessSpec

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
EMBEDDING_DIM = "1536"

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                  Knowledge base creation Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

def is_configured() -> bool:
    return bool(PINECONE_API_KEY and PINECONE_INDEX)


def _get_client():
    return Pinecone(api_key=PINECONE_API_KEY)


def ensure_index_exists():
    pc = _get_client()
    existing = [idx['name'] for idx in pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        pc.create_index(
            name = PINECONE_INDEX,
            dimension=1536,
            metric = "cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD , region=PINECONE_REGION)
        )

    return pc.Index(PINECONE_INDEX)


def upsert(vectors: List[Tuple[str, List[float], Dict[str, Any]]], namespace: str = "claimflow"):
    """
        Vector : list of (id , embedding , metadata)
    """
    index = ensure_index_exists()
    payload = [{"id" : vid , "values" : emb , "metadata" : meta} for vid , emb , meta in vectors]
    for i in range(0 , len(payload) , 100):
        index.upsert(vectors=payload[i : i + 100] , namespace=namespace)


def query(embedding : List[float] , top_k : int = 5 , filter : Dict[str , Any] = None , namespace : str = "claimflow"):
    index = ensure_index_exists()
    result = index.query(
        vector = embedding , top_k = top_k , include_metadata = True , filter = filter , namespace = namespace
    )
    return [
        {"score" : match['score'] , "metadata" : match.get("metadata" , {}) , "id" : match['id']} 
        for match in result.get("matches" , [])
    ]