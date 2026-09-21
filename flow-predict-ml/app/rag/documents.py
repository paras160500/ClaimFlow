"""
    Loads and chunks the synthetic knowledge base (policy docs + investigator notes)
    into (text , metadata) pairs ready for embedding/indexing.

    Chunking is intentionally simple (paragraph-based, on blank lines) since the
    source documents are short and already well structured no need for sliding
    windo chunker here.
"""



# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import os 
import re 
from typing import Any, Dict, List , Tuple

BASE_DIR = os.path.join(os.path.dirname(__file__) , ".." , ".." , "knowledge_base")
POLICY_DIR = os.path.join(BASE_DIR , "policy_docs")
NOTES_DIR = os.path.join(BASE_DIR , "investigator_notes")

_POLICY_FILENAME_RE = re.compile(r"^([a-z_]+?)_v(\d+)\.txt$")

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                  Document Processing statement
# ════════════════════════════════════════════════════════════════════════════════════════════════

def _chunk_paragraphs(text : str , min_len : int = 40) -> List[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [p for p in parts if len(p) >= min_len]


def load_policy_documents() -> List[Tuple[str , Dict[str , Any]]]:
    """
        Returns [(chunk_text , metadata) , ...] for every policy doc chunk
    """
    results = []
    if not os.path.isdir(POLICY_DIR):
        return results

    for filename in sorted(os.listdir(POLICY_DIR)):
        if not filename.endswith(".txt"):
            continue
        match = _POLICY_FILENAME_RE.match(filename)
        policy_type = match.group(1).upper() if match else filename.replace(".txt" , "").upper()
        version = f"V{match.group(2)}" if match else "V1"

        with open(os.path.join(POLICY_DIR , filename)) as f:
            content = f.read()

        for i , chunk in enumerate(_chunk_paragraphs(content)):
            section = chunk.split("\n" , 1)[0].rstrip(":").lower() if ":" in chunk.split("\n" , 1)[0] else "general"
            results.append((
                chunk,
                {
                    "document_type": "policy",
                    "policy_type": policy_type,
                    "policy_version": version,
                    "section": section,
                    "source_file": filename,
                    "chunk_index": i,
                },
            ))

    return results


def load_investigator_notes() -> List[Tuple[str , Dict[str , Any]]]:
    """
        Returns [(note_text , metadata) , ... ] one chunk per note
    """
    results = []
    if not os.path.isdir(NOTES_DIR):
        return results

    for filename in sorted(os.listdir(NOTES_DIR)):
        if not filename.endswith(".txt"):
            continue
        claim_id = filename.replace(".txt" , "")
        with open(os.path.join(NOTES_DIR , filename)) as f:
            content = f.read().strip()
        if content:
            results.append((
                content,
                {
                    "document_type": "investigator_note",
                    "claim_id": claim_id,
                    "source_file": filename,
                },
            ))

    return results 


def load_all_documents() -> List[Tuple[str , Dict[str , Any]]]:
    return load_policy_documents() + load_investigator_notes()