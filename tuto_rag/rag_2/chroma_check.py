import json
from chromadb import PersistentClient

PERSIST_DIR = "./chroma"
COLLECTION_NAME = "rag_chunks"

def check_collection():
    client = PersistentClient(path=PERSIST_DIR)
    
    try:
        col = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"❌ Collection '{COLLECTION_NAME}' introuvable: {e}")
        return
    count = col.count()
    print(f"\n📊 Collection: {COLLECTION_NAME}")
    print(f"   Nombre total: {count} documents")
    
    if count == 0:
        print("❌ Aucun document dans la collection")
        return

    result = col.get(
        limit=3,
        include=["documents", "metadatas", "embeddings"]
    )
    
    print(f"\n🔍 Échantillon (3 premiers documents):")
    print(f"   IDs: {result['ids'][:3]}")

    if result.get('documents'):
        print(f"\n✓ Documents présents:")
        for i, doc in enumerate(result['documents'][:3]):
            print(f"     [{i}] {doc[:100]}...")
    else:
        print("\n❌ Aucun document (texte)")

    if result.get('metadatas'):
        print(f"\n✓ Métadonnées présentes:")
        for i, meta in enumerate(result['metadatas'][:3]):
            print(f"     [{i}] {json.dumps(meta, ensure_ascii=False, indent=8)}")
    else:
        print("\n❌ Aucune métadonnée")
    
    if result.get('embeddings').all():
        print(f"\n✓ Embeddings présents:")
        for i, emb in enumerate(result['embeddings'][:3]):
            if emb.all():
                print(f"     [{i}] Vecteur de dimension {len(emb)} - premiers: {emb[:5]}")
            else:
                print(f"     [{i}] Vecteur vide!")
    else:
        print("\n❌ Aucun embedding (vecteur)")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    check_collection()
