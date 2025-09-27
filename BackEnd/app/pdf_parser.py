import requests
import certifi
import pdfplumber
from io import BytesIO
from typing import Dict
import re


class PDFParser:
    @staticmethod
    def download_pdf(url: str) -> BytesIO:
        """Download PDF and return as file-like object"""
        try:

            response = requests.get(url, verify=certifi.where(), timeout=10)
            response.raise_for_status()
        except requests.exceptions.SSLError:

            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
        return BytesIO(response.content)

    @staticmethod
    def parse_lenovo_specs(pdf_file: BytesIO) -> Dict:
        """Parse Lenovo PSREF PDF specifications"""
        specs = {}
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

            # Extract processor
            processor_match = re.search(r"Processor\s*([^\n]+)", text, re.IGNORECASE)
            if processor_match:
                specs["processor"] = processor_match.group(1).strip()

            # Extract memory
            memory_match = re.search(
                r"Memory.*?(\d+GB[^\n]*)", text, re.IGNORECASE | re.DOTALL
            )
            if memory_match:
                specs["memory"] = memory_match.group(1).strip()

            # Extract storage
            storage_match = re.search(r"Storage\s*([^\n]+)", text, re.IGNORECASE)
            if storage_match:
                specs["storage"] = storage_match.group(1).strip()

            # Extract display
            display_match = re.search(r"Display\s*([^\n]+)", text, re.IGNORECASE)
            if display_match:
                specs["display"] = display_match.group(1).strip()

            # Extract graphics
            graphics_match = re.search(r"Graphics\s*([^\n]+)", text, re.IGNORECASE)
            if graphics_match:
                specs["graphics"] = graphics_match.group(1).strip()

        return specs

    @staticmethod
    def parse_hp_specs(pdf_file: BytesIO) -> Dict:
        """Parse HP datasheet PDF specifications"""
        specs = {}
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

            # HP-specific parsing logic
            lines = text.split("\n")
            for i, line in enumerate(lines):
                line_lower = line.lower()

                if "processor" in line_lower and i + 1 < len(lines):
                    specs["processor"] = lines[i + 1].strip()

                if "memory" in line_lower and i + 1 < len(lines):
                    specs["memory"] = lines[i + 1].strip()

                if "storage" in line_lower and i + 1 < len(lines):
                    specs["storage"] = lines[i + 1].strip()

                if "display" in line_lower and i + 1 < len(lines):
                    specs["display"] = lines[i + 1].strip()

        return specs


# PDF URLs
CANONICAL_PDFS = {
    "lenovo_thinkpad_e14_intel": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_E14_Gen_5_Intel/ThinkPad_E14_Gen_5_Intel_Spec.PDF",
    "lenovo_thinkpad_e14_amd": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_E14_Gen_5_AMD/ThinkPad_E14_Gen_5_AMD_Spec.pdf",
    "hp_probook_450_g10": "https://h20195.www2.hp.com/v2/GetPDF.aspx/c08504822.pdf",
    "hp_probook_440_g11": "https://h20195.www2.hp.com/v2/getpdf.aspx/c08947328.pdf",
}

if __name__ == "__main__":
    parser = PDFParser()

    for name, url in CANONICAL_PDFS.items():
        print(f"\n--- Parsing {name} ---")
        try:
            pdf_file = parser.download_pdf(url)

            if "lenovo" in name:
                specs = parser.parse_lenovo_specs(pdf_file)
            else:
                specs = parser.parse_hp_specs(pdf_file)

            print("Extracted specs:", specs)
        except Exception as e:
            print(f"Failed to parse {name}: {e}")
