"""
    Unified retrieval interface used by the LLM layer.
    If the pinecone and openai api is there then it will
    find from the pinecone otherwise without failing it will
    provide local feedback using local TF-IDF index built by
    scripts/index_documents.py 
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import logging 
import os 
import pickle
from typing import Any,Dict, List, Optional 
from app.rag import embeddings , pinecone_client

logger = logging.getLogger("claimflow.rag.retriever")

LOCAL_INDEX_PATH = os.getenv(
    "LOCAL_RAG_INDEX_PATH" , 
    os.path.join(os.path.dirname(__file__) , ".." , ".." , "data" , "local_rag_index.pkl")
)

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                 Retriever Logic with pinecone
# ════════════════════════════════════════════════════════════════════════════════════════════════

class BaseRetriever:
    def retrieve(self , query : str , top_k : int = 5 , metadata_filter : Optional[Dict[str , Any]] = None) -> List[Dict[str , Any]]:
        raise NotImplementedError

class PineconeRetriever(BaseRetriever):
    def retrieve(self , query : str , top_k : int = 5 , metadata_filter : Optional[Dict[str , Any]] = None) -> List[Dict[str , Any]]:
        pc_filter = {k: {"$eq": v} for k, v in (metadata_filter or {}).items()}
        query_embedding = embeddings.get_embedding(query)
        matches = pinecone_client.query(query_embedding, top_k=top_k, filter=pc_filter or None)
        return [
            {"text": m["metadata"].get("text", ""), "metadata": m["metadata"], "score": m["score"]}
            for m in matches
        ]

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                 Retriever Logic with local
# ════════════════════════════════════════════════════════════════════════════════════════════════

class LocalTfidfRetriever(BaseRetriever):
    """
    Local, dependency-light fallback: TF-IDF + cosine similarity over the
    same chunked documents that would otherwise be embedded into Pinecone.
    Good enough for keyword-heavy queries like "comprehensive policy theft
    coverage" against a small, curated knowledge base -- it is not a
    semantic embedding search, and that trade-off should be visible to
    whoever's demoing this (the API response includes `"source": "local_fallback"`).
    """

    def __init__(self):
        self._vectorizer = None
        self._matrix = None
        self._texts: List[str] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._load()


    def _load(self):
        if not os.path.exists(LOCAL_INDEX_PATH):
            logger.warning(
                "No local RAG index found at %s. Run `python scripts/index_documents.py` "
                "to build one. Retrieval will return no results until then.",
                LOCAL_INDEX_PATH,
            )
            return
        with open(LOCAL_INDEX_PATH, "rb") as f:
            payload = pickle.load(f)
        self._vectorizer = payload["vectorizer"]
        self._matrix = payload["matrix"]
        self._texts = payload["texts"]
        self._metadatas = payload["metadatas"]


    def retrieve(self, query: str, top_k: int = 5,metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if self._vectorizer is None:
            return []

        from sklearn.metrics.pairwise import cosine_similarity

        candidate_idx = range(len(self._texts))
        if metadata_filter:
            candidate_idx = [
                i for i in candidate_idx
                if all(self._metadatas[i].get(k) == v for k, v in metadata_filter.items())
            ]
        if not candidate_idx:
            return []

        query_vec = self._vectorizer.transform([query])
        sub_matrix = self._matrix[list(candidate_idx)]
        scores = cosine_similarity(query_vec, sub_matrix)[0]

        ranked = sorted(zip(candidate_idx, scores), key=lambda t: -t[1])[:top_k]
        return [
            {"text": self._texts[i], "metadata": self._metadatas[i], "score": float(s), "source": "local_fallback"}
            for i, s in ranked
            if s > 0
        ]


_retriever_instance: Optional[BaseRetriever] = None


def _rag_is_configured() -> bool:
    from app.rag import pinecone_client
    return pinecone_client.is_configured() and bool(os.getenv("OPENAI_API_KEY"))


def get_retriever() -> BaseRetriever:
    global _retriever_instance
    if _retriever_instance is not None:
        return _retriever_instance

    if _rag_is_configured():
        try:
            _retriever_instance = PineconeRetriever()
            logger.info("RAG retriever: Pinecone (semantic embedding search)")
            return _retriever_instance
        except Exception as exc:  # noqa: BLE001
            logger.error("Pinecone retriever failed to initialize (%s); falling back to local index.", exc)

    _retriever_instance = LocalTfidfRetriever()
    logger.info("RAG retriever: local TF-IDF fallback")
    return _retriever_instance


def reset_retriever_cache():
    """Used by tests / after re-indexing to force get_retriever() to reload."""
    global _retriever_instance
    _retriever_instance = None
