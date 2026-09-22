import io
import zipfile
import pytest
from backend.services.material_processor import MaterialProcessor, ProcessedMaterial


def create_mock_pptx_bytes(slide_texts: list[str]) -> bytes:
    """Helper to create minimal valid PPTX zip file with slide XMLs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for idx, text in enumerate(slide_texts, start=1):
            slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p><a:r><a:t>{text}</a:t></a:r></a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
            zf.writestr(f"ppt/slides/slide{idx}.xml", slide_xml)
    buf.seek(0)
    return buf.read()


def create_mock_docx_bytes(paragraphs: list[str]) -> bytes:
    """Helper to create minimal valid DOCX zip file with document.xml."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        p_xml = "".join([f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs])
        doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>{p_xml}</w:body>
</w:document>"""
        zf.writestr("word/document.xml", doc_xml)
    buf.seek(0)
    return buf.read()


def test_process_txt_file():
    """Verify plain text extraction."""
    raw = b"Introduction to Algorithms and Data Structures.\nTopic: Binary Search."
    result = MaterialProcessor.process_material("notes.txt", raw)
    assert result.success is True
    assert result.material_type == "txt"
    assert "Binary Search" in result.content


def test_process_markdown_file():
    """Verify markdown extraction."""
    raw = b"# Lecture 1 Notes\n\n- Point 1: Fundamental Axioms\n- Point 2: Implementation"
    result = MaterialProcessor.process_material("lecture.md", raw)
    assert result.success is True
    assert result.material_type == "markdown"
    assert "Fundamental Axioms" in result.content


def test_process_pptx_slides():
    """Verify PPTX slide-by-slide text extraction with slide markers."""
    slides = [
        "Slide 1 Title: Core Principles",
        "Slide 2 Content: Detailed Conceptual Framework",
    ]
    pptx_bytes = create_mock_pptx_bytes(slides)
    result = MaterialProcessor.process_material("slides.pptx", pptx_bytes)

    assert result.success is True
    assert result.material_type == "pptx"
    assert result.page_or_slide_count == 2
    assert "[Slide 1]" in result.content
    assert "[Slide 2]" in result.content
    assert "Core Principles" in result.content
    assert "Detailed Conceptual Framework" in result.content


def test_process_docx_document():
    """Verify DOCX paragraph extraction."""
    paragraphs = [
        "Course Progression Syllabus",
        "Lecture 1 focuses on core algorithmic foundations.",
    ]
    docx_bytes = create_mock_docx_bytes(paragraphs)
    result = MaterialProcessor.process_material("syllabus.docx", docx_bytes)

    assert result.success is True
    assert result.material_type == "docx"
    assert "Course Progression Syllabus" in result.content
    assert "algorithmic foundations" in result.content


def test_process_corrupt_pptx_handled_gracefully():
    """Verify corrupt PPTX returns failure warning and does not raise an exception."""
    corrupt_bytes = b"This is not a zip container at all."
    result = MaterialProcessor.process_material("corrupted.pptx", corrupt_bytes)
    assert result.success is False
    assert len(result.warnings) > 0
    assert "corrupted" in result.warnings[0].lower() or "zip" in result.warnings[0].lower()


def test_process_unsupported_file_handled_gracefully():
    """Verify unsupported file extension returns warning and does not crash."""
    binary_data = b"\x00\x01\x02\x03\x04"
    result = MaterialProcessor.process_material("data.xyz_unknown", binary_data)
    assert result.success is False
    assert any("unsupported" in w.lower() for w in result.warnings)


def test_process_empty_file():
    """Verify empty 0-byte file returns clean warning."""
    result = MaterialProcessor.process_material("empty.txt", b"")
    assert result.success is False
    assert any("empty" in w.lower() for w in result.warnings)


def test_context_budget_truncation():
    """Verify excessively large material is truncated to protect context budget."""
    giant_text = "A" * (MaterialProcessor.MAX_CHARS_PER_DOCUMENT + 5000)
    result = MaterialProcessor.process_material("huge.txt", giant_text.encode("utf-8"))
    assert result.success is True
    assert len(result.content) < len(giant_text)
    assert any("truncated" in w.lower() for w in result.warnings)
