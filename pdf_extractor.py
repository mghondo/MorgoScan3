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
        if m_number_match:
            m_number_cell = m_number_match.group(2).strip()

            # Try to extract name from M Number Cell
            name_match = re.search(r'(?:- |-)([^-|]+)(?:\s*-|\s*\||$)', m_number_cell)
            if name_match:
                name = name_match.group(1).strip()
            else:
                # For cases where the name is at the end of the M Number Cell
                name_match = re.search(r'([^-]+)$', m_number_cell)
                if name_match:
                    name = name_match.group(1).strip()

            # Special cases
            if "Distillate Cart" in m_number_cell:
                name_parts = m_number_cell.split('-')
                if len(name_parts) >= 4:
                    name = f"{name_parts[-2].strip()} Distillate Cart"
            elif "Gummies" in m_number_cell:
                name = m_number_cell.split('-')[-1].strip()
            elif "Syrup" in m_number_cell or "Chocolate" in m_number_cell:
                name = m_number_cell.split('-')[-1].strip()

        # If name is still not found or needs refinement, try to extract from details
        if name == "Not found" or name.isdigit() or len(name) <= 2:
            if details != "Not found":
                name_match = re.search(r'(?:- |-)([^-|]+)(?:\s*-|\s*\||$)', details)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    # For cases where the name is at the beginning
                    name_match = re.search(r'Brand:[^-]+-([^-]+)', details)
                    if name_match:
                        name = name_match.group(1).strip()

        # Remove any trailing numbers or dashes
        name = re.sub(r'[-\d]+$', '', name).strip()

        # Extract strain information
        strain = "Not found"
        if m_number_match:
            m_number_cell = m_number_match.group(2).strip()
            if "Indica" in m_number_cell or "Indica" in details:
                strain = "Indica"
            elif "Sativa" in m_number_cell or "Sativa" in details:
                strain = "Sativa"
            elif "Hybrid" in m_number_cell or "Hybrid" in details:
                strain = "Hybrid"

        # Extract Type information
        type_info = "Undetermined"
        if m_number_match:
            combined_text = (m_number_cell + " " + details).lower()  # Convert to lowercase

            if any(weight in combined_text for weight in ["2.83", "5.66", "14.15", "28.3"]):
                type_info = "Flower"
            elif any(edible_type in combined_text for edible_type in ["gummies", "edibles", "drink"]):
                type_info = "Edibles"
            elif any(cartridge_type in combined_text for cartridge_type in ["distillate", "cart", "cartridge"]):
                type_info = "Cartridge"
            elif "edb oral" in combined_text:  # Check for case-insensitive match
                type_info = "Edibles"

        # Extract Days information from details
        days_match = re.search(r'Supply:\s*(\d+)', details, re.IGNORECASE)
        days = days_match.group(1) if days_match else "Not found"

        # Extract Weight information from details or M Number Cell
        weight = "Not found"

        # Check for specific weights first
        if any(weight_value in combined_text for weight_value in ["2.83", "5.66", "14.15", "28.3"]):
            weight_matches = [value for value in ["2.83", "5.66", "14.15", "28.3"] if value in combined_text]
            weight = weight_matches[0] if weight_matches else weight

        # If no specific weights are found, check for 'Wgt:'
        if weight == "Not found":
            wgt_match = re.search(r'Wgt:\s*(\d+\.?\d*)', details, re.IGNORECASE)  # Match Wgt: followed by a number
            weight = wgt_match.group(1) if wgt_match else weight

        if m_number_match:
            m_number = m_number_match.group(1)
            mnumber_cell = m_number_match.group(2).strip()
            extracted_items.append({
                "item_number": item_num,
                "package_id": package_id,
                "m_number": m_number,
                "MNumberCell": mnumber_cell,
                "Name": name,
                "details": details,
                "strain": strain,
                "type": type_info,
                "days": days,  # Add days to extracted items
                "weight": weight  # Add weight to extracted items
            })
        else:
            extracted_items.append({
                "item_number": item_num,
                "package_id": package_id,
                "m_number": "Not found",
                "MNumberCell": "Not found",
                "Name": name,
                "details": details,
                "strain": strain,
                "type": type_info,
                "days": days,  # Add days to extracted items
                "weight": weight  # Add weight to extracted items
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
                print(f"Product Details: {item['details']}")
                print(f"Name: ")

                # Print Type and Type of Flower sub-message if applicable
                print(f"Type: {item['type']}")

                if item['type'] == 'Flower':
                    print("Type of Flower: ")  # Leave blank for now

                print(f"Strain: {item['strain']}")
                print(f"Days: {item['days']}")  # Print days information
                print(f"Weight: {item['weight']}")  # Print weight information
                print(f"Expiration: ")

            print("\n" + "=" * 50 + "\n")


# Usage
manifest_directory = "ManifestDrop"
process_pdfs_in_directory(manifest_directory)