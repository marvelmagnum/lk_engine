import os
import fitz

import fitz  # PyMuPDF
import os

def extract_text_and_images(pdf_path, output_folder="output"):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Open the PDF file
    doc = fitz.open(pdf_path)
    extracted_text = ""
    image_count = 0

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Extract text
        text = page.get_text()
        extracted_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
        
        # Extract images
        images = page.get_images(full=True)
        
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            image_ext = base_image["ext"]
            image_count += 1

            # Save the image
            image_filename = f"{output_folder}/image_{page_num + 1}_{image_count}.{image_ext}"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_data)
    
    doc.close()
    
    # Save the extracted text to a file
    text_file_path = os.path.join(output_folder, "extracted_text.txt")
    with open(text_file_path, "w", encoding="utf-8") as text_file:
        text_file.write(extracted_text)
    
    print(f"Extraction completed! {image_count} images and text saved in '{output_folder}'.")

# Example usage
extract_text_and_images("sample.pdf")
