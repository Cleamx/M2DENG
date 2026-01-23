import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Tuple
from datetime import datetime
import fitz


class PDFLoader:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata = {
            'source_file': os.path.basename(file_path),
            'source_type': 'pdf'
        }
        self.raw_text = ""
        self.pages_data = []

    def load(self) -> Dict[str, Any]:

        print(f"\n📄 Chargement PDF (PyMuPDF): {self.file_path}")

        doc = fitz.open(self.file_path)
        self.metadata['num_pages'] = len(doc)

        for page_num, page in enumerate(doc, start=1):
            rect = page.rect
            page_height = rect.height

            blocks = page.get_text("blocks")

            cleaned_text = self._clean_headers_footers_geometric(
                blocks,
                page_height
            )

            self.pages_data.append({
                'page_num': page_num,
                'text': cleaned_text,
                'height': page_height,
                'width': rect.width
            })

        doc.close()

        self.raw_text = "\n\n".join([p['text'] for p in self.pages_data])

        print(
            f"  ✅ {len(self.raw_text)} caractères extraits sur {self.metadata['num_pages']} pages")

        return {
            'raw_text': self.raw_text,
            'metadata': self.metadata,
            'pages_data': self.pages_data
        }

    def _clean_headers_footers_geometric(
        self,
        blocks: list,
        page_height: float
    ) -> str:

        header_limit = page_height * 0.08
        footer_limit = page_height * 0.92

        filtered_blocks = []
        for b in blocks:
            if b[6] == 0:
                y0, y1 = b[1], b[3]
                y_center = (y0 + y1) / 2

                if header_limit < y_center < footer_limit:
                    filtered_blocks.append(b[4])

        cleaned_text = '\n'.join(filtered_blocks)

        noise_patterns = [
            'Doctrine',
            'www.legifrance.gouv.fr',
            'JURITEXT',
            'Identifiant Légifrance'
        ]

        for pattern in noise_patterns:
            if pattern in cleaned_text:
                lines = cleaned_text.split('\n')
                lines = [l for l in lines if pattern not in l]
                cleaned_text = '\n'.join(lines)

        return cleaned_text


class XMLLoader:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = None
        self.root = None
        self.namespaces = {}

    def load(self) -> Dict[str, Any]:
        print(f"\n📋 Chargement XML: {self.file_path}")

        self.tree = ET.parse(self.file_path)
        self.root = self.tree.getroot()

        self._detect_namespaces()

        metadata = self._extract_metadata_from_xml()

        content = self._extract_content_from_xml()

        print(f"  ✅ {len(content)} caractères extraits")

        return {
            'raw_text': content,
            'metadata': metadata,
            'source_type': 'xml',
            'source_file': os.path.basename(self.file_path)
        }

    def _detect_namespaces(self):
        if self.root.tag.startswith('{'):
            ns = self.root.tag[1:].split('}')[0]
            self.namespaces['default'] = ns

    def _extract_metadata_from_xml(self) -> Dict[str, Any]:

        metadata = {
            'source_file': os.path.basename(self.file_path),
            'source_type': 'xml'
        }

        metadata_tags = [
            'reference', 'Reference', 'REFERENCE',
            'juridiction', 'Juridiction', 'JURIDICTION',
            'date', 'Date', 'DATE',
            'numero', 'Numero', 'NUMERO',
            'type', 'Type', 'TYPE',
            'formation', 'Formation',
            'president', 'President',
            'dispositif', 'Dispositif'
        ]

        for tag in metadata_tags:
            elem = self.root.find(f".//{tag}")
            if elem is not None and elem.text:
                key = tag.lower()
                metadata[key] = elem.text.strip()

        if self.root.attrib:
            for key, value in self.root.attrib.items():
                metadata[f"attr_{key}"] = value

        return metadata

    def _extract_content_from_xml(self) -> str:
        content_parts = []

        def traverse(element, depth=0):
            skip_tags = ['reference', 'juridiction', 'date', 'numero']
            tag_name = element.tag.split('}')[-1].lower()

            if element.text and element.text.strip() and tag_name not in skip_tags:
                text = element.text.strip()

                if tag_name not in ['p', 'div', 'span']:
                    content_parts.append(f"[{tag_name}]: {text}")
                else:
                    content_parts.append(text)

            for child in element:
                traverse(child, depth + 1)

        traverse(self.root)

        return "\n".join(content_parts)


class JSONLoader:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = None

    def load(self) -> Dict[str, Any]:
        print(f"\n📊 Chargement JSON: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        metadata, content_text = self._transform_json(self.data)

        metadata['source_file'] = os.path.basename(self.file_path)
        metadata['source_type'] = 'json'

        print(f"  ✅ {len(content_text)} caractères générés")

        return {
            'raw_text': content_text,
            'metadata': metadata
        }

    def _transform_json(self, data: Dict, prefix="") -> Tuple[Dict, str]:
        metadata = {}
        content_parts = []

        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, (int, float, bool)):
                metadata[full_key] = value
            elif isinstance(value, str):
                if self._is_iso_date(value):
                    metadata[full_key] = value
                    content_parts.append(
                        f"{key.replace('_', ' ').title()}: {self._format_date(value)}"
                    )

                elif self._is_structured_field(key, value):
                    metadata[full_key] = value

                else:
                    content_parts.append(
                        f"{key.replace('_', ' ').title()}: {value}"
                    )
                    if len(value) < 100:
                        metadata[f"{full_key}_short"] = value[:100]

            elif isinstance(value, list):
                if value:
                    metadata[f"{full_key}_count"] = len(value)

                    items_str = ", ".join([str(v) for v in value])
                    content_parts.append(
                        f"{key.replace('_', ' ').title()}: {items_str}"
                    )

            elif isinstance(value, dict):
                nested_meta, nested_text = self._transform_json(
                    value, f"{full_key}.")
                metadata.update(nested_meta)
                if nested_text:
                    content_parts.append(
                        f"\n{key.replace('_', ' ').title()}:\n{nested_text}"
                    )

        content_text = "\n".join(content_parts)
        return metadata, content_text

    @staticmethod
    def _is_iso_date(value: str) -> bool:
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except:
            return False

    @staticmethod
    def _format_date(iso_date: str) -> str:
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            mois_fr = [
                '', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
            ]
            return f"{dt.day} {mois_fr[dt.month]} {dt.year}"
        except:
            return iso_date

    @staticmethod
    def _is_structured_field(key: str, value: str) -> bool:
        if any(k in key.lower() for k in ['id', 'code', 'ref', 'numero', 'num']):
            return True

        if len(value) < 50 and ' ' not in value:
            return True

        return False
