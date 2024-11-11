import pdfplumber
import re
import os

def extract_data_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    # Extract Originating Entity
    company_match = re.search(r'1\.\s*Outbound\s*Transporter\s*(.*?)\n', text, re.IGNORECASE)
    company = company_match.group(1) if company_match else "Not found"

    # Extract Drivers
    drivers = re.findall(r'Name of Person Transporting\s*(.*?)\n', text)
    drivers_str = " / ".join(drivers) if drivers else "Not found"

    # Extract Package IDs, M Numbers, and Names
    items = re.findall(r'(\d+)\.\s*Package\s*\|\s*Shipped(.*?)(?=\d+\.\s*Package\s*\|\s*Shipped|\Z)', text, re.DOTALL)

    extracted_items = []
    for item_num, item_text in items:
        package_id_match = re.search(r'(\dA\d+)', item_text)
        m_number_match = re.search(r'(M\d{11}):\s*(.*?)(?:\s*\(|$)', item_text, re.DOTALL)

        package_id = package_id_match.group(1) if package_id_match else "Not found"
        if m_number_match:
            m_number = m_number_match.group(1)
            name_details = m_number_match.group(2).strip()
            extracted_items.append({
                "item_number": item_num,
                "package_id": package_id,
                "m_number": m_number,
                "name": name_details
            })
        else:
            extracted_items.append({
                "item_number": item_num,
                "package_id": package_id,
                "m_number": "Not found",
                "name": "Not found"
            })

    return company, drivers_str, extracted_items

def process_pdfs_in_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            print(f"Processing {filename}...")
            company, drivers, items = extract_data_from_pdf(pdf_path)

            print(f"Company: {company}")
            print(f"Drivers: {drivers}")
            print(f"\nNumber of items: {len(items)}")

            for item in items:
                print(f"\nItem {item['item_number']}:")
                print(f"Package ID: {item['package_id']}")
                print(f"M Number: {item['m_number']}")
                print(f"Name: {item['name']}")

            print("\n" + "=" * 50 + "\n")

# Usage
manifest_directory = "ManifestDrop"
process_pdfs_in_directory(manifest_directory)git init