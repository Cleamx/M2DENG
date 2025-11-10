import re
import os
import json
import time
from collections import Counter
from typing import List, Tuple, Optional
from pathlib import Path

import fitz
import requests
from dotenv import load_dotenv


def extract_pages_text(pdf_path: str) -> List[str]:
    doc = fitz.open(pdf_path)
    pages = []
    for p in doc:
        pages.append(p.get_text("text"))
    doc.close()
    return pages


def top_bottom_lines(text: str, max_lines: int = 3) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    lines = [l.rstrip() for l in text.splitlines() if l.strip() != ""]
    top = tuple(lines[:max_lines]) if lines else tuple()
    bottom = tuple(lines[-max_lines:]) if lines else tuple()
    return top, bottom


def detect_common_headers_footers(pages: List[str], max_lines: int = 3, threshold: float = 0.6) -> Tuple[List[str], List[str]]:
    top_counter = Counter()
    bottom_counter = Counter()
    n = len(pages) or 1
    for t in pages:
        top, bottom = top_bottom_lines(t, max_lines)
        if top:
            top_counter["\n".join(top)] += 1
        if bottom:
            bottom_counter["\n".join(bottom)] += 1

    headers = [k for k, v in top_counter.items() if v / n >= threshold]
    footers = [k for k, v in bottom_counter.items() if v / n >= threshold]
    return headers, footers


def remove_header_footer(text: str, headers: List[str], footers: List[str]) -> str:
    s = text.strip("\n")
    for h in headers:
        if h and s.startswith(h):
            s = s[len(h):].lstrip("\n")
    for f in footers:
        if f and s.endswith(f):
            s = s[:-len(f)].rstrip("\n")
    return s


def split_in_two(pages: List[str]) -> Tuple[str, str]:
    mid = max(1, len(pages) // 2)
    first = "\n\n".join(pages[:mid])
    second = "\n\n".join(pages[mid:])
    return first, second


def build_messages_for_extraction(text: str) -> List[dict]:
    system_msg = (
        "You are a document parser. Extract metadata and return a single valid JSON object only (no extra text). "
        "Required fields: metadata (object with title, author, date, president, doc_type, other), "
        "content (array of objects {\"part\": str, \"text\": str}). "
        "If a field is not present, set it to null or empty. Keep the text cleaned."
    )
    user_msg = f"Document text:\n\n{text}"

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]


def call_mistral_api(messages: List[dict], api_key: str, model: str = "mistral-small-2506", max_tokens: int = 2048) -> str:
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()

    if "choices" in data and len(data["choices"]) > 0:
        return data["choices"][0]["message"]["content"]

    return json.dumps(data)


def extract_json_from_text(s: str) -> Optional[dict]:
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = s[start: i + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    pass
    return None


def process_single_pdf(pdf_path: str, api_key: str) -> dict:
    model = "mistral-small-latest"
    pages = extract_pages_text(pdf_path)
    headers, footers = detect_common_headers_footers(pages)
    cleaned_pages = [remove_header_footer(p, headers, footers) for p in pages]
    joined = "\n\n".join(cleaned_pages)
    
    match = re.search(r'(Texte[\s_-]*int[ée]gral[\s:]*)(.*)', joined, re.IGNORECASE | re.DOTALL)
    if match:
        full_text = match.group(2).strip()
    else:
        full_text = ""

    first_half, second_half = split_in_two(cleaned_pages)

    messages1 = build_messages_for_extraction(first_half)
    messages2 = build_messages_for_extraction(second_half)

    resp1 = call_mistral_api(messages1, api_key, model)
    resp2 = call_mistral_api(messages2, api_key, model)

    json1 = extract_json_from_text(resp1) or {"metadata": {}, "content": [
        {"part": "1", "text": resp1}]}
    json2 = extract_json_from_text(resp2) or {"metadata": {}, "content": [
        {"part": "2", "text": resp2}]}

    merged = {"metadata": {}, "content": []}
    for k in set(list(json1.get("metadata", {}).keys()) + list(json2.get("metadata", {}).keys())):
        v1 = json1.get("metadata", {}).get(k)
        v2 = json2.get("metadata", {}).get(k)
        merged["metadata"][k] = v1 if v1 not in (None, "", []) else v2

    merged_content = []
    for c in json1.get("content", []):
        merged_content.append(c)
    for c in json2.get("content", []):
        merged_content.append(c)
    merged["content"] = merged_content

    merged["_detected_headers"] = headers
    merged["_detected_footers"] = footers
    merged["_source_file"] = pdf_path
    merged["full_text"] = full_text

    return merged


def process_pdf_list(pdf_paths: List[str], out_path: str) -> None:
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY not found in environment (.env)")

    results = []
    for i, pdf_path in enumerate(pdf_paths, 1):
        print(f"Traitement du PDF {i}/{len(pdf_paths)}: {pdf_path}")
        try:
            result = process_single_pdf(pdf_path, api_key)
            results.append(result)
            print(f"  ✓ Terminé")
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
            results.append({
                "_source_file": pdf_path,
                "_error": str(e),
                "metadata": {},
                "content": []
            })
        time.sleep(10)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nRésultats sauvegardés dans: {out_path}")


def main():

    folder_path = Path('docs/pdf/')
    if not folder_path.exists():
        print(f"Erreur: Le dossier '{folder_path}' n'existe pas.")
        return

    if not folder_path.is_dir():
        print(f"Erreur: '{folder_path}' n'est pas un dossier.")
        return

    pdf_files = sorted(folder_path.glob("*.pdf"))
    if not pdf_files:
        print(f"Aucun fichier PDF trouvé dans '{folder_path}'")
        return

    print(f"Trouvé {len(pdf_files)} fichier(s) PDF dans '{folder_path}'")

    output_file = "output.json"

    pdf_paths = [str(pdf) for pdf in pdf_files]

    process_pdf_list(pdf_paths, output_file)


if __name__ == "__main__":
    main()
