import json
from pathlib import Path
from typing import List, Dict


def chunk_text(text: str, chunk_size: int = 500, overlap_chars: int = 100) -> List[str]:
    chunks = []
    i = 0
    text_length = len(text)
    
    while i < text_length:
        chunk_end = min(i + chunk_size, text_length)
        chunk = text[i:chunk_end]
        if i > 0 and overlap_chars > 0:
            overlap_start = max(0, i - overlap_chars)
            overlap_prefix = text[overlap_start:i]
            chunk = overlap_prefix + chunk
        
        chunks.append(chunk)
        i += chunk_size
    
    return chunks


def process_json_file(json_path: str, chunk_size: int = 500) -> List[Dict]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict) and "Document" in data:
        data = [data["Document"]]

    if not isinstance(data, list):
        data = [data]
    
    results = []
    for doc in data:
        full_text = doc.get('full_text', '')
        if not full_text and 'Decision' in doc:
            decision = doc.get('Decision', {})
            if isinstance(decision, dict) and 'Texte_Integral' in decision:
                texte_integral = decision['Texte_Integral']
                if isinstance(texte_integral, dict):
                    full_text = texte_integral.get('__text', '')
        
        metadata = doc.get('metadata', {})
        if not metadata:
            metadata = {
                'Donnees_Techniques': doc.get('Donnees_Techniques', {}),
                'Dossier': doc.get('Dossier', {}),
                'Audience': doc.get('Audience', {})
            }
        
        source_file = doc.get('_source_file', '') or doc.get('Donnees_Techniques', {}).get('Identification', json_path)
        if not full_text:
            continue
        
        chunks = chunk_text(full_text, chunk_size)
        
        for idx, chunk in enumerate(chunks, 1):
            results.append({
                'chunk_id': f"{Path(source_file).stem}_chunk_{idx}",
                'chunk_index': idx,
                'total_chunks': len(chunks),
                'text': chunk,
                'metadata': metadata,
                '_source_file': source_file
            })
    
    return results
def main():
    chunk_size = 500
    all_chunks = []

    json_folder = Path('docs/json/')
    if json_folder.exists() and json_folder.is_dir():
        json_files = sorted(json_folder.glob("*.json"))
        print(f"Trouvé {len(json_files)} fichier(s) JSON dans {json_folder}")

        for json_file in json_files:
            print(f"\nTraitement de {json_file.name}...")
            try:
                chunks = process_json_file(str(json_file), chunk_size)
                all_chunks.extend(chunks)
                print(f"  → {len(chunks)} chunks créés")
            except Exception as e:
                print(f"  ✗ Erreur: {e}")
    else:
        print(f"Le dossier {json_folder} n'existe pas.")

    pdf_json = Path('output.json')
    if pdf_json.exists():
        print(f"\nTraitement de {pdf_json}...")
        try:
            chunks = process_json_file(str(pdf_json), chunk_size)
            all_chunks.extend(chunks)
            print(f"  → {len(chunks)} chunks créés")
        except Exception as e:
            print(f"  ✗ Erreur: {e}")

    xml_json = Path('output_xml.json')
    if xml_json.exists():
        print(f"\nTraitement de {xml_json}...")
        try:
            chunks = process_json_file(str(xml_json), chunk_size)
            all_chunks.extend(chunks)
            print(f"  → {len(chunks)} chunks créés")
        except Exception as e:
            print(f"  ✗ Erreur: {e}")

    output_file = 'chunks.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"Total : {len(all_chunks)} chunks créés")
    print(f"Résultats sauvegardés dans : {output_file}")

if __name__ == "__main__":
    main()
