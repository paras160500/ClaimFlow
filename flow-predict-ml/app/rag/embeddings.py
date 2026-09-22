"""
    Generate the embedding of the documents we have
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os 
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL" , "text-embedding-3-small")

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                  Knowledge base creation Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

def get_embeddings(texts : List[str]) -> List[List[float]]:
    # We can do from openai import OpenAI here for lazy import to not crash the app if we dont have api key
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.embeddings.create(model = EMBEDDING_MODEL , input = texts)
    return [item.embedding for item in resp.data]


def get_embedding(text : str) -> List[float]:
    return get_embeddings([text])[0]