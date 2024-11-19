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

    # Extract Package IDs, M Numbers, Names, and Details
    items = re.findall(r'(\d+)\.\s*Package\s*\|\s*Shipped(.*?)(?=\d+\.\s*Package\s*\|\s*Shipped|\Z)', text, re.DOTALL)

    extracted_items = []
    for item_num, item_text in items:
        package_id_match = re.search(r'(\dA\d+)', item_text)
        m_number_match = re.search(r'(M\d{11}):\s*(.*?)(?:\s*\(|$)', item_text, re.DOTALL)
        details_match = re.search(r'(?:Brand|Wet|Qty).*', item_text, re.IGNORECASE)

        package_id = package_id_match.group(1) if package_id_match else "Not found"
        details = details_match.group(0) if details_match else "Not found"

        # Extract Name from Product Details
        name = "Not found"
        if details.startswith("Brand:"):
            parts = details.split('-')
            if len(parts) >= 4:
                name = parts[-2].strip()
            elif len(parts) == 3:
                name = parts[-1].split('|')[0].strip()
        elif details.startswith("Brand"):
            parts = details.split('-')
            if len(parts) >= 3:
                name = parts[-2].strip()

        if m_number_match:
            m_number = m_number_match.group(1)
            mnumber_cell = m_number_match.group(2).strip()
            extracted_items.append({
                "item_number": item_num,
                "package_id": package_id,
                "m_number": m_number,
                "MNumberCell": mnumber_cell,
                "Name": name,  # Add the extracted Name
                "details": details
            })
        else:
            extracted_items.append({
                "item_number": item_num,
                "package_id": package_id,
                "m_number": "Not found",
                "MNumberCell": "Not found",
                "Name": name,  # Add the extracted Name
                "details": details
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
                print(f"M Number Cell: {item['MNumberCell']}")
                print(f"Name: {item['Name']}")  # Print the extracted Name
                print(f"Product Details: {item['details']}")

            print("\n" + "=" * 50 + "\n")


# Usage
manifest_directory = "ManifestDrop"
process_pdfs_in_directory(manifest_directory)