"""
    Indexes the knowledge base (policy doc + investigator notes) for retrieval.

    python scripts/index_documents.py

    - If pinecone and openai api is there then it will embed the chunks
    and push it to the pinecone vectordb
    - If we dont provide any api then it will write into the local_rag_index.pkl
    so retrieval still works with zero external credentials.
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os 
import pickle
import sys 
from dotenv import load_dotenv
load_dotenv()

sys.path.insert( 0 , os.path.join(os.path.dirname(__file__) , ".."))

from app.rag.documents import load_all_documents

LOCAL_INDEX_PATH = os.getenv("LOCAL_RAG_INDEX_PATH" , os.path.join(os.path.dirname(__file__) , ".." , "data" , "local_rag_index.pkl"))

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                 Indexing logic local & pinecone
# ════════════════════════════════════════════════════════════════════════════════════════════════

def _pinecone_ready() -> bool:
    return bool(os.getenv("PINECONE_API_KEY") and os.getenv("PINECONE_INDEX") and os.getenv("OPENAI_API_KEY"))

def index_into_pinecone(documents):
    from app.rag import embeddings, pinecone_client
    print(f"Embedding {len(documents)} chunk with OPENAI embedding model...")
    texts = [text for text, _ in documents]

    vectors = []
    batch_size = 100
    for i in range(0 , len(texts) , batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_meta = [documents[i+j][1] for j in range(len(batch_texts))]
        batch_embeddings = embeddings.get_embeddings(batch_texts)
        for j , emb in enumerate(batch_embeddings):
            meta = dict(batch_meta[j])
            meta['text'] = batch_texts[j]   # Store text in metadata so that retrieval can be easy
            vector_id = f"{meta.get('document_type', 'doc')}-{meta.get('source_file', i + j)}-{meta.get('chunk_index', 0)}"
            vectors.append((vector_id , emb , meta))
        print(f"  embedded {min(i + batch_size, len(texts))}/{len(texts)}")

    print(f"Upserting {len(vectors)} vectors into Pinecone index '{os.environ['PINECONE_INDEX']}'...")
    pinecone_client.upsert(vectors)
    print("Done. Pinecone index is ready for retrieval.")


def index_locally(documents):
    from sklearn.feature_extraction.text import TfidfVectorizer

    print(f"Building local TF-IDF index over {len(documents)} chunks "
          "(no PINECONE_API_KEY/OPENAI_API_KEY found)...")
    texts = [text for text, _ in documents]
    metadatas = [meta for _, meta in documents]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=20000, ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(texts)

    os.makedirs(os.path.dirname(LOCAL_INDEX_PATH), exist_ok=True)
    with open(LOCAL_INDEX_PATH, "wb") as f:
        pickle.dump(
            {"vectorizer": vectorizer, "matrix": matrix, "texts": texts, "metadatas": metadatas}, f
        )
    print(f"Done. Local fallback index written to {LOCAL_INDEX_PATH}")


def main():
    documents = load_all_documents()
    if not documents:
        print("No documents found. Run `python knowledge_base/build_knowledge_base.py` first.")
        sys.exit(1)

    print(f"Loaded {len(documents)} chunks "
          f"({sum(1 for _, m in documents if m['document_type'] == 'policy')} policy, "
          f"{sum(1 for _, m in documents if m['document_type'] == 'investigator_note')} investigator notes)")

    if _pinecone_ready():
        index_into_pinecone(documents)
    else:
        index_locally(documents)


if __name__ == "__main__":
    main()