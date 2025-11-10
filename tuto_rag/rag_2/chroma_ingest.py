import json
import os
from pathlib import Path
from typing import List, Dict, Any

try:
    from chromadb import PersistentClient
except ImportError:
    PersistentClient = None

INPUT_FILES = [
    "chunks_vectorized.json"
]
PERSIST_DIR = "./chroma"
COLLECTION_NAME = "rag_chunks"
RESET_COLLECTION = True
BATCH_SIZE = 200

def load_vectors() -> List[Dict[str, Any]]:
    for p in INPUT_FILES:
        path = Path(p)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError(
                    "Le JSON doit être une liste d'objets {content, payload, vec}")
            print(f"Chargé {len(data)} éléments depuis {p}")
            return data
    raise FileNotFoundError(
        f"Aucun fichier trouvé parmi: {', '.join(INPUT_FILES)}")

def ensure_chromadb_installed():
    if PersistentClient is None:
        raise RuntimeError("Installez 'chromadb' (pip install chromadb)")

def simple_meta(payload: Dict[str, Any]) -> Dict[str, Any]:
    src = ""
    idx = 0
    if isinstance(payload, dict):
        src = str(payload.get("_source_file", ""))
        try:
            idx = int(payload.get("chunk_index", 0))
        except Exception:
            idx = 0
    return {
        "source": src,
        "chunk_index": idx,
        "meta_json": json.dumps(payload or {}, ensure_ascii=False),
    }

def ingest_simple():
    ensure_chromadb_installed()
    items = load_vectors()

    os.makedirs(PERSIST_DIR, exist_ok=True)
    client = PersistentClient(path=PERSIST_DIR)

    if RESET_COLLECTION:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Collection '{COLLECTION_NAME}' réinitialisée")
        except Exception:
            pass

    col = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    total = len(items)
    added = 0
    gid = 0
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = items[start:end]

        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []
        embeds: List[List[float]] = []

        for it in batch:
            vec = it.get("vec", [])
            if not isinstance(vec, list) or not vec:
                continue
            ids.append(f"doc-{gid}")
            gid += 1
            docs.append(str(it.get("content", "")))
            metas.append(simple_meta(it.get("payload", {}) or {}))
            embeds.append(vec)

        if ids:
            col.add(ids=ids, documents=docs,
                    metadatas=metas, embeddings=embeds)
            added += len(ids)
            print(f"  → {added}/{total} insérés")

    print("\n✓ Ingestion simple terminée.")
    print(f"  Persist dir: {PERSIST_DIR}")
    print(f"  Collection:  {COLLECTION_NAME}")

if __name__ == "__main__":
    ingest_simple()
