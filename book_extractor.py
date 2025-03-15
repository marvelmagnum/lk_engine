import os
import re
import fitz  # PyMuPDF

def extract_text_and_images(pdf_path, output_folder="output"):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Open the PDF file
    doc = fitz.open(pdf_path)
    extracted_text = ""
    image_count = 0

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Extract text with font information
        text_blocks = page.get_text("dict")["blocks"]
        
        for block in text_blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        font_name = span["font"]  # Get the font name
                        
                        # Check if the text is bold (font name contains "Bold")
                        if "Bold" in font_name:
                            text = f"<b>{text}</b>"
                        # Check if the text is italic (font name contains "Italic")
                        elif "Italic" in font_name:
                            text = f"<i>{text}</i>"
                        
                        extracted_text += text
                    extracted_text += "\n"  # Add a newline after each line
        
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

    extracted_text = remove_header_footer(extracted_text)
    extracted_text = find_tables(extracted_text)
    extracted_text = join_text(extracted_text)
    
    # Save the extracted text to a file
    text_file_path = os.path.join(output_folder, "extracted_text.txt")
    with open(text_file_path, "w", encoding="utf-8") as text_file:
        text_file.write(extracted_text)
    
    print(f"Extraction completed! {image_count} images and text saved in '{output_folder}'.")

def remove_header_footer(text):
    lines = text.split('\n')
    header = lines[0]
    footer = lines[1]

    processed = ""
    for index, line in enumerate(lines):
        # add the header/footer at the top of the file once
        # add any lines that are not that afterwards
        if index < 2  or (line != header and line != footer):
            processed += line + '\n'
      
    return processed

def find_tables(text):
    lines = text.split('\n')

    processed = ""
    in_table = False
    table_line_count = 0
    for index, line in enumerate(lines):
        if line.startswith("<i>") and line.endswith("</i>") and "Opponent" in line:
            processed += "<td>\n" + line + '\n'
            in_table = True
            table_line_count += 1
            continue
        
        if in_table:
          if table_line_count % 4 == 0: # table entries are always 4 lines. so the 1st line after a set of 4 is the one to watch for
              table_line_count += 1
              processed += line + '\n'
              continue
          else:
            if line == '\t':  # Tables end with a tab on a line
                table_line_count = 0
                in_table = False
                processed += "</td>\n" + line
                continue
        
        processed += line + '\n'
    
    return processed

                

def join_text(text):
    lines = text.split('\n')
    
    processed = ""
    section = ""
    in_table = False

    for index, line in enumerate(lines):
        
        if index < 2:
            processed += line + '\n'
            continue
        
        if line.startswith("<b>") and line.endswith("</b>"):
            if section != "":
              processed += section + '\n'
              section = ""
            processed += line + '\n'
            continue
        
        if line == "<td>":
            if section != "":
              processed += section + '\n'
              section = ""
            in_table = True
            processed += line + '\n'
            continue
        
        if in_table:
            processed += line + '\n'
            if line == "</td>":
                in_table = False
            continue

        if line.startswith("<i>") and line.endswith("</i>"):
            if section != "":
              processed += section + '\n'
              section = ""
            processed += line + '\n'
            continue
        
        if line == '\t':
            processed += section + '\n'
            section = ""
            continue
        
        section += line

    if section != "":
        processed += section + '\n'

    return processed


# Example usage
extract_text_and_images("sample.pdf")