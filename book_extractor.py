import os
import re
import fitz  # PyMuPDF
from tkinter import Tk
from tkinter.filedialog import askopenfilename

def extract_text_and_images(pdf_path):
    full_path = os.path.realpath(__file__)
    output_path = os.path.dirname(full_path) + "\\output"
    image_path = os.path.dirname(full_path) + "\\data"

    # Create output folder if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(image_path, exist_ok=True)
    
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
            image_filename = f"{image_path}/image_{image_count:03}_p{page_num + 1}_.{image_ext}"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_data)
    
    doc.close()

    extracted_text = remove_header_footer(extracted_text)
    extracted_text = remove_continued(extracted_text)
    extracted_text = find_tables(extracted_text)
    
    # Save the extracted text to a file
    text_file_path = os.path.join(output_path, "extracted_text.txt")
    with open(text_file_path, "w", encoding="utf-8") as text_file:
        text_file.write(extracted_text)
    
    print(f"Extraction completed! {image_count} images and text saved in '{output_path}'.")


def remove_header_footer(text):
    lines = text.split('\n')
    header = lines[0]
    footer = lines[1]

    processed = ""
    for index, line in enumerate(lines):
        # add the header/footer at the top of the file once
        # add any lines that are not that afterwards
        if index < 2:
            if ("<b>" in line and "</b>" in line):
                line = line.replace("<b>", "")
                line = line.replace("</b>", "")
            processed +=  line.title() + '\n'
            continue

        if (not header in line and not footer in line):
            processed += line + '\n'
      
    return processed

def remove_continued(text):
    lines = text.split('\n')

    processed = ""
    for index, line in enumerate(lines):
        if line != '(continued...)':
            processed += line + '\n'
        else:
            test = line

    return processed

def find_tables(text):
    lines = text.split('\n')

    processed = ""
    in_combat_table = False
    in_market_table = False
    skip_lines = 0
    table_line_count = 0
    for index, line in enumerate(lines):
        # Process combat tables
        if line.startswith("<i>") and line.endswith("</i>") and "Opponent" in line:
            processed += "<tc>\n" + line + '\n'
            in_combat_table = True
            table_line_count += 1
            continue
        
        if in_combat_table:
          if table_line_count % 4 == 0: # combat table entries are always 4 lines. so the 1st line after a set of 4 is the one to watch for
              table_line_count += 1
              processed += line + '\n'
              continue
          else:
            if line == '\t' or len(line) > 20:  # Tables end with a tab on a line or the line after the table is a full line (assuming over 20 chars)
                table_line_count = 0
                in_combat_table = False
                processed += "</tc>\n" + line
                continue

        # Process market tables
        if skip_lines > 0:
            skip_lines -= 1
            continue

        if line.startswith("<i>") and line.endswith("</i>") and "Item" in line:
            if not in_market_table: # new table - mark it up
                processed += "<tm>\n" + line + '\n'
                in_market_table = True
                table_line_count += 1
                continue
            else: # same table with inset headers - remove it (don't write)
                skip_lines = 2  # mark the next 2 lines to be skipped
                continue
        
        if in_market_table:
          if table_line_count % 3 == 0: # market table entries are always 3 lines. so the 1st line after a set of 3 is the one to watch for
              table_line_count += 1
              processed += line + '\n'
              continue
          else:
            if line == '\t' or len(line) > 40:  # Tables end with a tab on a line or the line after the table is a full line (assuming over 20 chars)
                table_line_count = 0
                in_market_table = False
                processed += "</tm>\n" + line
                continue
        
        processed += line + '\n'
    
    return processed

def select_pdf_from_folder():
    # Hide the root window
    Tk().withdraw()
    
    # Open a file dialog and allow only PDF files
    file_path = askopenfilename(
        initialdir="path/to/your/folder",
        title="Select a PDF file",
        filetypes=[("PDF Files", "*.pdf")]
    )
    
    if file_path:
        print(f"You selected: {file_path}")
        return file_path
    else:
        print("No file selected.")
        return None



# Example usage
extract_text_and_images(select_pdf_from_folder())