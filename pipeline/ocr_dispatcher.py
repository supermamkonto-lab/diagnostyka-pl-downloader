"""OCR dispatcher — placeholder, activated when ocr.enabled = true in config."""

from pathlib import Path
from typing import Optional
from database.delta_manager import DeltaManager


class OcrDispatcher:
    def __init__(self, config: dict, delta: DeltaManager, logger):
        self.config = config
        self.delta = delta
        self.log = logger
        self._enabled = config.get("ocr", {}).get("enabled", False)
        self._engine = config.get("ocr", {}).get("engine", "tesseract")
        self._lang = config.get("ocr", {}).get("language", "pol+eng")

    def process(self, portal_id: str, portal_document_id: str, pdf_path: str) -> Optional[str]:
        if not self._enabled:
            self.log.debug("OCR disabled — skipping")
            return None

        out_path = Path(pdf_path).with_suffix(".txt")
        try:
            if self._engine == "tesseract":
                return self._tesseract(pdf_path, str(out_path))
            else:
                self.log.warning(f"Unknown OCR engine: {self._engine}")
                return None
        except Exception as e:
            self.log.error(f"OCR failed for {pdf_path}: {e}")
            return None

    def _tesseract(self, pdf_path: str, out_path: str) -> str:
        import subprocess
        # pdf2image → tesseract pipeline
        try:
            from pdf2image import convert_from_path
            import pytesseract
        except ImportError:
            raise RuntimeError("pdf2image and pytesseract required for OCR: pip install pdf2image pytesseract")

        pages = convert_from_path(pdf_path, dpi=300)
        text_parts = []
        for page_img in pages:
            text_parts.append(pytesseract.image_to_string(page_img, lang=self._lang))

        full_text = "\n\n--- PAGE BREAK ---\n\n".join(text_parts)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        return out_path
