import logging
import tqdm
import os
import pytesseract
import fitz  
from PIL import Image
import io

from pdf2image import convert_from_path


class OCRConverter:
    def __init__(self):
        self.pdf_aspect_map = {
                "Bipolar-Disorder-A-Guide.pdf": "Mania",
                "Coping-with-Trauma-Related-Dissociation.pdf": "Dissociation",
                "Feeling-Good-The-New-Mood-Therapy.pdf": "Depression",
                "New-Harbinger-Self-Help-Workbook-The-Addiction-Recovery-Skills.pdf": "Substance Use",
                "Night-Falls-Fast-Understanding-Suicide.pdf": "Suicidal",
                "Overcoming-Harm-OCD.pdf": "Repetitive Thought",
                "RelasiSehat.pdf": "General",
                "Say-Good-Night-to-Insomnia.pdf": "Sleep Disturbance",
                "The-Anger-Workbook.pdf": "Anger",
                "The-Anxiety-and-Phobia-Workbook.pdf": "Anxiety",
                "The-Body-Keeps-the-Score-PDF.pdf": "Somatic",
                "The-Science-of-Successful-Learning.pdf": "Memory",
                "Understanding-Psychosis-and-Schizophrenia.pdf": "Psychosis"
        }
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(base_dir, "data", "text_files")
        self.pdfs_dir = os.path.join(base_dir, "..", "..", "external_data", "pdf")
        self.vectorstore_dir = os.path.join(base_dir, "..", "..", "vectorstore")


    def convert_all_pdfs(self):
        logging.info("OCR Converter: Starting conversion of all PDFs")
        files = self.pdf_aspect_map.keys()

        os.makedirs(self.files_dir, exist_ok=True)

        for file_name in tqdm.tqdm(files, desc="Converting PDFs", unit="file"):
            aspect = self.pdf_aspect_map[file_name]
            pdf_path = os.path.join(self.pdfs_dir, file_name)
            out_file = os.path.join(self.files_dir, f"{aspect}.txt")

            if os.path.exists(out_file):
                logging.info(f"Skipping {file_name} (already processed)")
                continue

            if not os.path.exists(pdf_path):
                logging.error(f"PDF not found: {pdf_path}")
                continue

            text = "" 

            try:
                text = self.convert_single_pdf(pdf_path)
            except Exception as err:
                logging.error(f"Failed OCR on {file_name}: {err}")

            if not text.strip():
                logging.warning(f"No text extracted for {file_name}, skipping...")
                continue

            try:
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(text)
                logging.info(f"Saved: {out_file}")
            except Exception as err:
                logging.error(f"Failed saving {out_file}: {err}")
    

    def convert_single_pdf(self, pdf_path):
        logging.info(f"OCR Converter: Reading {pdf_path}")

        text_output = []

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            with tqdm.tqdm(total=total_pages, desc=f"{os.path.basename(pdf_path)}", leave=False) as pbar:
                for page_num, page in enumerate(doc):
                    page_text = page.get_text()

                    if page_text and page_text.strip():
                        text_output.append(page_text)
                    else:
                        logging.info(f"Page {page_num} empty → using OCR")

                        pix = page.get_pixmap()
                        img_bytes = pix.tobytes("png")
                        image = Image.open(io.BytesIO(img_bytes))

                        ocr_text = pytesseract.image_to_string(image, lang='eng')
                        text_output.append(ocr_text)

                    pbar.update(1)

            doc.close()

        except Exception as e:
            logging.error(f"fitz failed → fallback full OCR: {e}")

            pages = convert_from_path(pdf_path, dpi=150)  
            total_pages = len(pages)

            with tqdm.tqdm(total=total_pages, desc=f"OCR {os.path.basename(pdf_path)}", leave=False) as pbar:
                for i, page in enumerate(pages):
                    page_text = pytesseract.image_to_string(page, lang='eng')
                    text_output.append(page_text)

                    page.close()
                    pbar.update(1)

        return "\n".join(text_output)