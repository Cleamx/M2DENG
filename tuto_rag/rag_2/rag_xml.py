import re
import os
import json
from pathlib import Path

import json
from pathlib import Path
import xml.etree.ElementTree as ET

def extract_metadata_and_text_from_xml(xml_path: str) -> dict:
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        meta = {}
        for section in ["Donnees_Techniques", "Dossier", "Audience"]:
            node = root.find(section)
            if node is not None:
                meta[section] = {child.tag: (child.text or '').strip() for child in node}
        full_text = ""
        texte_integral_node = root.find("Texte_Integral")
        if texte_integral_node is not None:
            full_text = ET.tostring(texte_integral_node, encoding='unicode', method='text')
        
        if not full_text:
            for elem in root.iter():
                tag = elem.tag.lower()
                if "texte" in tag and "integral" in tag:
                    full_text = ET.tostring(elem, encoding='unicode', method='text')
                    break
        
        full_text = re.sub(r"\s+", " ", full_text).strip()
        return {
            "metadata": meta,
            "full_text": full_text,
            "_source_file": xml_path
        }
    except Exception as e:
        print(f"Erreur extraction XML {xml_path}: {e}")
        return {
            "metadata": {},
            "full_text": "",
            "_source_file": xml_path,
            "_error": str(e)
        }

def process_xml_list(xml_paths, out_path):
    results = []
    for i, xml_path in enumerate(xml_paths, 1):
        print(f"Traitement du XML {i}/{len(xml_paths)}: {xml_path}")
        result = extract_metadata_and_text_from_xml(xml_path)
        results.append(result)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nRésultats sauvegardés dans: {out_path}")

def main():
    folder_path = Path('docs/xml/')
    if not folder_path.exists():
        print(f"Erreur: Le dossier '{folder_path}' n'existe pas.")
        return
    if not folder_path.is_dir():
        print(f"Erreur: '{folder_path}' n'est pas un dossier.")
        return
    xml_files = sorted(folder_path.glob("*.xml"))
    if not xml_files:
        print(f"Aucun fichier XML trouvé dans '{folder_path}'")
        return
    print(f"Trouvé {len(xml_files)} fichier(s) XML dans '{folder_path}'")
    output_file = "output_xml.json"
    xml_paths = [str(xml) for xml in xml_files]
    process_xml_list(xml_paths, output_file)

if __name__ == "__main__":
    main()
