import json
import os
import time
from pathlib import Path
from typing import List, Dict

import requests
from dotenv import load_dotenv

def load_chunks(chunks_file: str = "chunks.json") -> List[Dict]:
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    return chunks

def _get_mistral_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Erreur: variable d'environnement MISTRAL_API_KEY introuvable. Ajoutez-la dans votre .env.")
    return api_key


def _mistral_embed_batch(texts: List[str], model: str, api_key: str, timeout: int = 60, retries: int = 3) -> List[List[float]]:
    url = "https://api.mistral.ai/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    backoff = 1.5
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                url,
                headers=headers,
                json={"model": model, "input": texts},
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", [])
                items.sort(key=lambda x: x.get("index", 0))
                return [it.get("embedding", []) for it in items]

            if resp.status_code in (429, 500, 502, 503, 504):
                wait = backoff ** attempt
                print(f"⚠️ API Mistral {resp.status_code}, tentative {attempt}/{retries}. Nouvelle tentative dans {wait:.1f}s...")
                time.sleep(wait)
                continue

            print(f"❌ Erreur API Mistral {resp.status_code}: {resp.text}")
            return []
        except requests.RequestException as e:
            wait = backoff ** attempt
            print(f"⚠️ Erreur réseau ({e}), tentative {attempt}/{retries}. Retry dans {wait:.1f}s...")
            time.sleep(wait)

    print("❌ Échec des appels à l'API Embeddings après plusieurs tentatives.")
    return []


def vectorize_chunks(chunks: List[Dict], model_name: str = "mistral-embed", batch_size: int = 64) -> List[Dict]:
    api_key = _get_mistral_api_key()
    if not api_key:
        return []

    print(f"Appel Mistral Embeddings avec le modèle: {model_name}")

    texts = [c.get("text", "") for c in chunks]
    vectors: List[List[float]] = []

    total = len(texts)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_texts = texts[start:end]
        print(f"  → Batch {start+1}-{end} / {total}")
        batch_vecs = _mistral_embed_batch(batch_texts, model_name, api_key)
        if not batch_vecs or len(batch_vecs) != len(batch_texts):
            print("❌ Échec ou taille inattendue du batch d'embeddings. Arrêt.")
            return []
        vectors.extend(batch_vecs)

    dim = len(vectors[0]) if vectors else 0
    print(f"  Dimension renvoyée par le modèle: {dim}")
    target_dim = 1024
    if dim != target_dim:
        print(f"  Ajustement des vecteurs vers {target_dim} dimensions (pad/troncature)")
        fixed = []
        for v in vectors:
            if len(v) < target_dim:
                v = v + [0.0] * (target_dim - len(v))
            elif len(v) > target_dim:
                v = v[:target_dim]
            fixed.append(v)
        vectors = fixed

    vectorized: List[Dict] = []
    for i, ch in enumerate(chunks):
        payload = {
            "chunk_id": ch.get("chunk_id", ""),
            "chunk_index": ch.get("chunk_index", 0),
            "total_chunks": ch.get("total_chunks", 0),
            "metadata": ch.get("metadata", {}),
            "_source_file": ch.get("_source_file", ""),
        }
        vectorized.append({
            "content": ch.get("text", ""),
            "payload": payload,
            "vec": vectors[i],
        })

    return vectorized

def save_vectorized_chunks(vectorized_chunks: List[Dict], output_file: str = "chunks_vectorized.json"):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(vectorized_chunks, f, ensure_ascii=False, indent=2)
    print(f"\n✓ {len(vectorized_chunks)} chunks vectorisés sauvegardés dans: {output_file}")
    
    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"  Taille du fichier: {file_size:.2f} MB")

def main():
    chunks_file = "chunks.json"
    output_file = "chunks_vectorized.json"
    model_name = "mistral-embed"

    if not Path(chunks_file).exists():
        print(f"❌ Erreur: {chunks_file} n'existe pas.")
        print("Exécutez d'abord chunker.py pour créer les chunks.")
        return

    print(f"Chargement de {chunks_file}...")
    chunks = load_chunks(chunks_file)
    print(f"  → {len(chunks)} chunks chargés")
    
    if not chunks:
        print("❌ Aucun chunk trouvé.")
        return

    vectorized_chunks = vectorize_chunks(chunks, model_name)
    
    if not vectorized_chunks:
        return
    save_vectorized_chunks(vectorized_chunks, output_file)
    
    print("\n" + "="*50)
    print("✓ Vectorisation terminée avec succès!")
    print(f"  Modèle utilisé: {model_name}")
    if vectorized_chunks:
        print(f"  Dimension des embeddings: {len(vectorized_chunks[0]['vec'])}")

if __name__ == "__main__":
    main()
