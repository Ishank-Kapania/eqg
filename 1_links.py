import os
import xml.etree.ElementTree as ET

def process_xml_file(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    urls = []
    for paper in root.findall('.//paper'):
        url_element = paper.find('url')
        if url_element is not None and url_element.text:
            url_content = url_element.text
            full_url = f"https://aclanthology.org/{url_content}.pdf"
            urls.append(full_url)
    return urls
def save_urls(filename, urls):
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}_urls.txt"
    with open(output_filename, 'w') as f:
        for url in urls:
            f.write(f"{url}\n")
    print(f"URLs saved to {output_filename}")
# Process all XML files in the current directory
for filename in os.listdir('.'):
    if filename.endswith('.xml'):
        print(f"Processing {filename}...")
        urls = process_xml_file(filename)
        save_urls(filename, urls)
