import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ProcessedMaterial:
    """Represents the structured text extracted from an academic supporting material."""
    name: str
    material_type: str
    content: str
    page_or_slide_count: int = 0
    warnings: List[str] = field(default_factory=list)
    success: bool = True


class MaterialProcessor:
    """
    Modular processing layer for academic supporting documents.
    Extracts text while preserving page/slide boundaries, handles corrupt/unsupported
    files gracefully, and enforces size limits.
    """
    MAX_CHARS_PER_DOCUMENT = 35000  # Context budget protection (~8000 tokens)

    # XML namespaces for PPTX and DOCX
    A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

    @classmethod
    def process_material(
        cls,
        name: str,
        file_bytes: bytes,
        file_type: Optional[str] = None
    ) -> ProcessedMaterial:
        """
        Detects document format and routes to appropriate extraction handler.
        Never crashes on corrupt or invalid files; records failure in warnings instead.
        """
        if not file_bytes:
            return ProcessedMaterial(
                name=name,
                material_type=file_type or "unknown",
                content="",
                success=False,
                warnings=[f"Supporting material '{name}' is empty (0 bytes)."]
            )

        # Detect extension
        ext = (file_type or Path(name).suffix.lower().lstrip(".")).lower()
        if ext.startswith("."):
            ext = ext[1:]

        try:
            if ext == "pdf":
                return cls.process_pdf(file_bytes, name)
            elif ext in ("pptx", "ppt"):
                return cls.process_pptx(file_bytes, name)
            elif ext in ("docx", "doc"):
                return cls.process_docx(file_bytes, name)
            elif ext in ("txt", "text"):
                return cls.process_txt(file_bytes, name)
            elif ext in ("md", "markdown"):
                return cls.process_markdown(file_bytes, name)
            else:
                return ProcessedMaterial(
                    name=name,
                    material_type=ext,
                    content="",
                    success=False,
                    warnings=[
                        f"Unsupported material format '{ext}' for file '{name}'. "
                        "Supported formats are: PDF, PPTX, DOCX, TXT, Markdown."
                    ]
                )
        except Exception as exc:
            return ProcessedMaterial(
                name=name,
                material_type=ext,
                content="",
                success=False,
                warnings=[f"Failed to process '{name}': {str(exc)}"]
            )

    @classmethod
    def process_pdf(cls, file_bytes: bytes, name: str) -> ProcessedMaterial:
        """
        Extracts text from PDF page by page, preserving [Page X] headers.
        Uses pypdf if installed, with a standard stream fallback.
        """
        warnings = []
        pages_text = []

        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
            for idx, page in enumerate(reader.pages, start=1):
                txt = page.extract_text() or ""
                cleaned = txt.strip()
                if cleaned:
                    pages_text.append(f"[Page {idx}]\n{cleaned}")
            
            content = "\n\n".join(pages_text)
            content = cls._truncate_if_needed(content, warnings, name)
            return ProcessedMaterial(
                name=name,
                material_type="pdf",
                content=content,
                page_or_slide_count=total_pages,
                warnings=warnings,
                success=True
            )
        except ImportError:
            # Fallback pure-python basic PDF text-stream reader
            try:
                raw = file_bytes.decode("latin-1", errors="ignore")
                # Look for stream ... endstream blocks or text tokens
                extracted_lines = []
                for match in re.finditer(r"\(([^\)]+)\)\s*Tj", raw):
                    extracted_lines.append(match.group(1))
                content = "\n".join(extracted_lines)
                if not content.strip():
                    content = "[PDF text stream extracted without external library]"
                warnings.append(
                    f"pypdf package not found; extracted partial raw streams for '{name}'."
                )
                return ProcessedMaterial(
                    name=name,
                    material_type="pdf",
                    content=cls._truncate_if_needed(content, warnings, name),
                    page_or_slide_count=1,
                    warnings=warnings,
                    success=True
                )
            except Exception as e:
                return ProcessedMaterial(
                    name=name,
                    material_type="pdf",
                    content="",
                    success=False,
                    warnings=[f"Could not parse PDF '{name}': {str(e)}"]
                )
        except Exception as exc:
            return ProcessedMaterial(
                name=name,
                material_type="pdf",
                content="",
                success=False,
                warnings=[f"Corrupted or invalid PDF file '{name}': {str(exc)}"]
            )

    @classmethod
    def process_pptx(cls, file_bytes: bytes, name: str) -> ProcessedMaterial:
        """
        Extracts text from PPTX slide by slide, preserving [Slide X] markers.
        Uses native ZIP + OpenXML parsing without requiring heavy compiled C-dependencies.
        """
        warnings = []
        slides_text = []

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                # Find all slide xml files
                slide_names = [f for f in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml", f)]
                # Sort numerically by slide number
                slide_names.sort(
                    key=lambda s: int(re.search(r"slide(\d+)\.xml", s).group(1))
                )

                if not slide_names:
                    warnings.append(f"PPTX file '{name}' contains no readable slides.")
                    return ProcessedMaterial(
                        name=name,
                        material_type="pptx",
                        content="",
                        page_or_slide_count=0,
                        warnings=warnings,
                        success=True
                    )

                for idx, s_name in enumerate(slide_names, start=1):
                    slide_xml = zf.read(s_name)
                    root = ET.fromstring(slide_xml)
                    
                    # Extract all drawing text elements <a:t>
                    text_elements = []
                    for elem in root.iter(f"{cls.A_NS}t"):
                        if elem.text and elem.text.strip():
                            text_elements.append(elem.text.strip())

                    slide_content = " ".join(text_elements).strip()
                    if slide_content:
                        slides_text.append(f"[Slide {idx}]\n{slide_content}")

            content = "\n\n".join(slides_text)
            content = cls._truncate_if_needed(content, warnings, name)

            return ProcessedMaterial(
                name=name,
                material_type="pptx",
                content=content,
                page_or_slide_count=len(slide_names),
                warnings=warnings,
                success=True
            )
        except zipfile.BadZipFile:
            return ProcessedMaterial(
                name=name,
                material_type="pptx",
                content="",
                success=False,
                warnings=[f"Corrupted or invalid PPTX file '{name}' (not a valid zip container)."]
            )
        except Exception as exc:
            return ProcessedMaterial(
                name=name,
                material_type="pptx",
                content="",
                success=False,
                warnings=[f"Failed to extract PPTX text from '{name}': {str(exc)}"]
            )

    @classmethod
    def process_docx(cls, file_bytes: bytes, name: str) -> ProcessedMaterial:
        """
        Extracts text from DOCX documents preserving paragraph and table structure.
        Uses native ZIP + OpenXML parsing without external C-extensions.
        """
        warnings = []
        paragraphs = []

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                if "word/document.xml" not in zf.namelist():
                    return ProcessedMaterial(
                        name=name,
                        material_type="docx",
                        content="",
                        success=False,
                        warnings=[f"DOCX '{name}' missing standard word/document.xml entry."]
                    )
                
                doc_xml = zf.read("word/document.xml")
                root = ET.fromstring(doc_xml)

                # Iterate through all paragraph nodes <w:p>
                for p in root.iter(f"{cls.W_NS}p"):
                    p_texts = [t.text for t in p.iter(f"{cls.W_NS}t") if t.text]
                    line = "".join(p_texts).strip()
                    if line:
                        paragraphs.append(line)

            content = "\n\n".join(paragraphs)
            content = cls._truncate_if_needed(content, warnings, name)

            return ProcessedMaterial(
                name=name,
                material_type="docx",
                content=content,
                page_or_slide_count=1,
                warnings=warnings,
                success=True
            )
        except zipfile.BadZipFile:
            return ProcessedMaterial(
                name=name,
                material_type="docx",
                content="",
                success=False,
                warnings=[f"Corrupted or invalid DOCX file '{name}'."]
            )
        except Exception as exc:
            return ProcessedMaterial(
                name=name,
                material_type="docx",
                content="",
                success=False,
                warnings=[f"Failed to extract DOCX text from '{name}': {str(exc)}"]
            )

    @classmethod
    def process_txt(cls, file_bytes: bytes, name: str) -> ProcessedMaterial:
        """Extracts text from plain text files with robust encoding fallback."""
        warnings = []
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = file_bytes.decode("latin-1")
                warnings.append(f"Decoded '{name}' using latin-1 encoding fallback.")
            except Exception:
                content = file_bytes.decode("utf-8", errors="replace")
                warnings.append(f"Decoded '{name}' with replacement characters for invalid bytes.")

        content = cls._truncate_if_needed(content.strip(), warnings, name)
        return ProcessedMaterial(
            name=name,
            material_type="txt",
            content=content,
            page_or_slide_count=1,
            warnings=warnings,
            success=True
        )

    @classmethod
    def process_markdown(cls, file_bytes: bytes, name: str) -> ProcessedMaterial:
        """Processes markdown documents."""
        mat = cls.process_txt(file_bytes, name)
        mat.material_type = "markdown"
        return mat

    @classmethod
    def _truncate_if_needed(cls, text: str, warnings: List[str], name: str) -> str:
        """Protects context budget by truncating excessively large materials."""
        if len(text) > cls.MAX_CHARS_PER_DOCUMENT:
            warnings.append(
                f"Material '{name}' exceeded context budget limit ({len(text)} chars); "
                f"truncated to first {cls.MAX_CHARS_PER_DOCUMENT} characters."
            )
            return (
                text[:cls.MAX_CHARS_PER_DOCUMENT]
                + f"\n\n[... Truncated remainder of '{name}' due to context budget limits ...]"
            )
        return text
