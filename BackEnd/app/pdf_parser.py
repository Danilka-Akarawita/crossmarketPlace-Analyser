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
        """Parse Lenovo PSREF PDF specifications (extended)"""
        specs = {}
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

            # Processor
            processor_match = re.search(r"Processor Family\s*(.+)", text, re.IGNORECASE)
            if processor_match:
                specs["processor_family"] = processor_match.group(1).strip()

            cpu_models = re.findall(r"(Core i[357]-\d{4,5}[A-Z]?)", text)
            if cpu_models:
                specs["processor_models"] = list(set(cpu_models))

            # Graphics
            graphics_match = re.findall(r"(Intel® UHD Graphics|Intel® Iris® Xe Graphics|NVIDIA® GeForce MX\d+)", text)
            if graphics_match:
                specs["graphics_options"] = list(set(graphics_match))

            # Operating System
            os_match = re.findall(r"(Windows® 11 [^\n]+|Ubuntu Linux|No preload operating system)", text)
            if os_match:
                specs["os_options"] = list(set(os_match))

            # Memory
            memory_match = re.search(r"Max Memory\s*([^\n]+)", text, re.IGNORECASE)
            if memory_match:
                specs["max_memory"] = memory_match.group(1).strip()

            mem_type = re.search(r"Memory Type\s*([^\n]+)", text, re.IGNORECASE)
            if mem_type:
                specs["memory_type"] = mem_type.group(1).strip()

            # Storage
            storage_match = re.search(r"Max Storage Support[^\n]*\s*([^\n]+)", text, re.IGNORECASE)
            if storage_match:
                specs["max_storage"] = storage_match.group(1).strip()

            storage_types = re.findall(r"M\.2 \d{4} SSD [^\n]+", text)
            if storage_types:
                specs["storage_types"] = storage_types

            # Display
            display_options = re.findall(r"14\" [^\n]+", text)
            if display_options:
                specs["display_options"] = display_options

            # Audio
            if "Dolby Atmos" in text:
                specs["speakers"] = "Stereo speakers, Dolby Atmos"
            if "Dolby Voice" in text:
                specs["microphone"] = "Dual-microphone array, Dolby Voice"

            # Camera
            camera_options = re.findall(r"(720p|1080p(?: \+ IR)?)", text)
            if camera_options:
                specs["camera_options"] = camera_options

            # Battery
            battery_match = re.findall(r"(\d{2}Wh Rechargeable Li-ion Battery[^\n]*)", text)
            if battery_match:
                specs["battery_options"] = battery_match

            battery_life = re.findall(r"MobileMark® 2018: up to [^\n]+", text)
            if battery_life:
                specs["battery_life"] = battery_life

            # Power adapter
            adapter_match = re.findall(r"65W USB-C®.*", text)
            if adapter_match:
                specs["power_adapter"] = adapter_match

            # Dimensions & Weight
            dim_match = re.search(r"Dimensions.*?\(([^\)]+)\)", text, re.IGNORECASE)
            if dim_match:
                specs["dimensions"] = dim_match.group(1).strip()

            weight_match = re.findall(r"Starting at [\d\.]+ kg", text)
            if weight_match:
                specs["weight"] = weight_match

            # Case materials & colors
            case_match = re.findall(r"(Arctic grey|Graphite black)", text, re.IGNORECASE)
            if case_match:
                specs["case_colors"] = list(set(case_match))

            # Connectivity
            wlan_match = re.findall(r"(Wi-Fi® 6E?.*?Bluetooth® [\d\.]+)", text)
            if wlan_match:
                specs["wireless"] = wlan_match

            ports = re.findall(r"(USB [^\n]+|Thunderbolt™ 4[^\n]+|HDMI® [^\n]+|RJ-45|Headphone / microphone combo)", text)
            if ports:
                specs["ports"] = list(set(ports))

            # Security
            if "TPM 2.0" in text:
                specs["security_chip"] = "TPM 2.0"
            if "fingerprint reader" in text:
                specs["fingerprint_reader"] = True
            if "Windows® Hello" in text:
                specs["windows_hello"] = True

            # Certifications
            eco_certs = re.findall(r"(ENERGY STAR® 8.0|EPEAT™ Gold|TCO Certified 9.0|RoHS compliant)", text)
            if eco_certs:
                specs["green_certifications"] = eco_certs

            if "MIL-STD-810H" in text:
                specs["mil_certification"] = "MIL-STD-810H passed"

        return specs

    @staticmethod
    def parse_hp_specs(pdf_file: BytesIO) -> Dict:
        """Parse HP datasheet PDF specifications (extended)"""
        specs = {}
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

            # Processor family & models
            proc_family = re.search(r"Processor family\s*([\s\S]+?)Available Processors", text, re.IGNORECASE)
            if proc_family:
                specs["processor_family"] = proc_family.group(1).strip()

            cpu_models = re.findall(r"Intel® Core™ i[357]-\d{4,5}[A-Z]?", text)
            if cpu_models:
                specs["processor_models"] = list(set(cpu_models))

            if "Intel® Pentium" in text:
                specs.setdefault("processor_models", []).append("Intel Pentium U300")

            # Graphics
            graphics_match = re.findall(r"(Intel® UHD Graphics|Intel® Iris® Xᶱ Graphics|NVIDIA® GeForce RTX™ 2050)", text)
            if graphics_match:
                specs["graphics_options"] = list(set(graphics_match))

            # Operating Systems
            os_match = re.findall(r"(Windows 11 [^\n]+|FreeDOS)", text)
            if os_match:
                specs["os_options"] = list(set(os_match))

            # Memory
            max_mem = re.search(r"Maximum memory\s*([^\n]+)", text, re.IGNORECASE)
            if max_mem:
                specs["max_memory"] = max_mem.group(1).strip()

            mem_slots = re.search(r"Memory slots\s*([^\n]+)", text, re.IGNORECASE)
            if mem_slots:
                specs["memory_slots"] = mem_slots.group(1).strip()

            # Storage
            storage = re.findall(r"(?:\d+ GB|\d+ TB) PCIe® NVMe™ [^\n]+", text)
            if storage:
                specs["storage_types"] = storage
            max_storage = re.search(r"Internal storage\s*([^\n]+)", text, re.IGNORECASE)
            if max_storage:
                specs["max_storage"] = max_storage.group(1).strip()

            # Display
            display_opts = re.findall(r"15\.6\" [^\n]+", text)
            if display_opts:
                specs["display_options"] = display_opts

            # Audio
            if "Dual stereo speakers" in text:
                specs["speakers"] = "Dual stereo speakers"
            if "dual array microphones" in text:
                specs["microphone"] = "Dual array microphones"

            # Camera
            cam_opts = re.findall(r"(720p HD camera|IR Camera|5MP camera)", text, re.IGNORECASE)
            if cam_opts:
                specs["camera_options"] = list(set(cam_opts))

            # Battery
            battery = re.findall(r"(\d{2} Wh [^\n]+Battery)", text)
            if battery:
                specs["battery_options"] = battery

            # Power adapter
            adapters = re.findall(r"HP Smart \d+ W [^\n]+adapter", text)
            if adapters:
                specs["power_adapter"] = adapters

            # Dimensions & Weight
            dims = re.search(r"Dimensions\s*([^\n]+)", text, re.IGNORECASE)
            if dims:
                specs["dimensions"] = dims.group(1).strip()

            weight = re.search(r"Weight\s*Starting at ([^\n]+)", text, re.IGNORECASE)
            if weight:
                specs["weight"] = weight.group(1).strip()

            # Connectivity
            wlan = re.findall(r"(Intel® Wi-Fi 6E [^\n]+|Realtek Wi-Fi 6E [^\n]+)", text)
            if wlan:
                specs["wireless"] = wlan

            ports = re.findall(r"(USB Type-[AC][^\n]+|HDMI 2\.1|RJ-45|headphone/microphone combo)", text, re.IGNORECASE)
            if ports:
                specs["ports"] = list(set([p.strip() for p in ports]))

            # Ethernet
            eth = re.search(r"(10/100/1000 GbE NIC)", text)
            if eth:
                specs["ethernet"] = eth.group(1)

            # Security
            if "TPM 2.0" in text:
                specs["security_chip"] = "TPM 2.0"
            if "Fingerprint sensor" in text:
                specs["fingerprint_reader"] = True
            if "IR Camera" in text:
                specs["windows_hello"] = True

            # Certifications
            eco = re.findall(r"(ENERGY STAR® certified|EPEAT® Gold|TCO Certified)", text)
            if eco:
                specs["green_certifications"] = eco
            if "MIL-STD" in text:
                specs["mil_certification"] = "MIL-STD tested"

            # Sustainability
            if "recycled" in text.lower():
                specs["environmental_materials"] = ["Recycled plastics, packaging, low halogen"]

        return specs


# PDF URLs
CANONICAL_PDFS = {
    "lenovo_thinkpad_e14_intel": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_E14_Gen_5_Intel/ThinkPad_E14_Gen_5_Intel_Spec.PDF",
    "lenovo_thinkpad_e14_amd": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_E14_Gen_5_AMD/ThinkPad_E14_Gen_5_AMD_Spec.pdf",
    "hp_probook_450_g10": "https://h20195.www2.hp.com/v2/GetPDF.aspx/c08504822.pdf",
    "hp_probook_440_g11": "https://h20195.www2.hp.com/v2/getpdf.aspx/c08947328.pdf",
}

# if __name__ == "__main__":
#     parser = PDFParser()

#     for name, url in CANONICAL_PDFS.items():
#         print(f"\n--- Parsing {name} ---")
#         try:
#             pdf_file = parser.download_pdf(url)

#             if "lenovo" in name:
#                 specs = parser.parse_lenovo_specs(pdf_file)
#             else:
#                 specs = parser.parse_hp_specs(pdf_file)

#             print("Extracted specs:", specs)
#         except Exception as e:
#             print(f"Failed to parse {name}: {e}")
