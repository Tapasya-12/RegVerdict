"""
Phase 1 - Step 1: PDF -> raw text, page by page.

Why pdfplumber over PyMuPDF here: pdfplumber gives easier access to
per-line text ordering, which matters for clause-header detection.
PyMuPDF is faster and better for scanned/rotated PDFs, so it's kept as
an optional fallback if pdfplumber returns near-empty pages (a sign the
PDF is scanned and needs OCR later).
"""

import pdfplumber
import fitz  # PyMuPDF
from pathlib import Path
from config import RAW_PDF_DIR, PROCESSED_DIR


def extract_with_pdfplumber(pdf_path: Path) -> list[dict]:
    """Returns list of {page_number, text} dicts.

    Uses layout=True so leading whitespace reflects each line's horizontal
    position on the page. clause_chunker.py relies on that indentation to
    tell true top-level clause headers apart from more-indented nested
    sub-list items that reuse the same "N. " numbering format.
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(layout=True) or ""
            pages.append({"page_number": i, "text": text})
    return pages


def extract_with_pymupdf(pdf_path: Path) -> list[dict]:
    """Fallback extractor, used when pdfplumber output looks too sparse."""
    pages = []
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc, start=1):
        pages.append({"page_number": i, "text": page.get_text()})
    doc.close()
    return pages


def is_suspiciously_empty(pages: list[dict], min_chars_per_page: int = 40) -> bool:
    """Heuristic: if most pages have almost no extracted text, the PDF is
    likely scanned/image-based and needs OCR (Tesseract) — flagged per the
    roadmap's risk table, not solved here."""
    if not pages:
        return True
    empty_count = sum(1 for p in pages if len(p["text"].strip()) < min_chars_per_page)
    return empty_count / len(pages) > 0.5


def parse_pdf(pdf_path: Path) -> list[dict]:
    pages = extract_with_pdfplumber(pdf_path)
    if is_suspiciously_empty(pages):
        print(f"[WARN] {pdf_path.name}: sparse text via pdfplumber, trying PyMuPDF fallback")
        pages = extract_with_pymupdf(pdf_path)
        if is_suspiciously_empty(pages):
            print(f"[WARN] {pdf_path.name}: still sparse — this PDF is likely scanned. "
                  f"Needs OCR (Tesseract) before it can be chunked. Skipping for now.")
    return pages


def parse_all_pdfs() -> dict[str, list[dict]]:
    """Parses every PDF in data/raw_pdfs/. Returns {filename: pages}."""
    results = {}
    pdf_files = list(RAW_PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[INFO] No PDFs found in {RAW_PDF_DIR}. "
              f"Drop RBI Master Direction PDFs there before running ingestion.")
        return results

    for pdf_path in pdf_files:
        print(f"[INFO] Parsing {pdf_path.name} ...")
        results[pdf_path.stem] = parse_pdf(pdf_path)
    return results


if __name__ == "__main__":
    all_pages = parse_all_pdfs()
    for name, pages in all_pages.items():
        total_chars = sum(len(p["text"]) for p in pages)
        print(f"{name}: {len(pages)} pages, {total_chars} chars extracted")
