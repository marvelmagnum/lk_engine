import re
import os

book = ""

def parse_section(section_text):
    # Extract the section number (it appears at the start of the section)
    section_number_match = re.search(r'^(\d+)\s*$', section_text.split('\n')[0].strip())
    if not section_number_match:
        return None
    
    # Adjust the section number by subtracting the offset
    section_number = str(int(section_number_match.group(1)))
    
    # Extract the text content (everything after the section number)
    text_content = '\n'.join(section_text.split('\n')[1:]).strip()
    ref_text = "".join(text_content.split('\n'))

    # correct book specific errors
    if "valley of bones" in book.lower():
        if section_number == "142": # a market table item has all columns in the same row. no CRLF between columns. 
            start_idx = text_content.find("<b>Masterwork Greatsword (Fighting +4)*</b>\t ")
            idx = start_idx + len("<b>Masterwork Greatsword (Fighting +4)*</b>\t ") # Also this item is abnormally big as a result causing an incorrect table end. Fix that.
            text_content = text_content[:start_idx - len("</tm>\n")] + text_content[start_idx:idx] + '\n' + text_content[idx:idx + 2] + '\n' +  text_content[idx + 2:]
            end_idx = text_content.find("When you have finished here,")
            text_content = text_content[:end_idx] + "</tm>\n" + text_content[end_idx:] # Finally mark table end at the correct spot
        if section_number == "488": # a stray " instead of an opening “ that breaks the csv load
            text_content = text_content.replace('"', '“')
        if section_number == "550": # incorrect italicized "Health" where the last letter got missed
            text_content = text_content.replace("<i>Healt</i>h", "<i>Health</i>")
    
    # Find all "Turn to/ turn to <number>" references
    references = re.findall(r'[Tt]urn(?:ing)? (?:back )?to[ ]?<b>[ ]?(\d+)[., )]*</b>', ref_text)
 
    # Adjust the references by subtracting the offset
    references = [str(int(ref)) for ref in references]
    
    # Count the number of references
    num_references = len(references)
    
    # Prepare the output row
    output_row = [
        section_number,
        '"' + text_content + '"',
        str(num_references),
        *references,
        '""'
    ]
    
    return output_row

def extract_book_name(section_text):
    # Extract the book name from the first section
    # The book name is split across two lines, e.g.:
    # – Legendary Kingdoms –
    # – THE VALLEY OF BONES –
    book_name_parts = re.findall(r'–\s*(.*?)\s*–', section_text)
    if len(book_name_parts) >= 2:
        # Combine the two parts with a hyphen and convert the second part to Title Case
        book_name = f"{book_name_parts[0]} - {book_name_parts[1].title()}"
        global book
        book = book_name
        return book_name
    return None

def convert_to_csv(input_file, output_file):
    full_path = os.path.realpath(__file__)
    input_path = os.path.dirname(full_path) + "\\output\\" + input_file
    output_path = os.path.dirname(full_path) + "\\data\\" + output_file
    with open(input_path, 'r', encoding='utf-8') as infile:
        content = infile.read()
    
    # Split the content into sections based on the section number pattern
    # Each section starts with a number followed by a newline
    sections = re.split(r'\n<b>(\d+)\t?<\/b>\n', content)
    
    
    # Extract the book name from the first section
    if sections:
        first_section_content = sections[0]  # Content of the first section
        book_name = extract_book_name(first_section_content)
    
    # Remove empty sections and group section numbers with their content
    sections = [(sections[i], sections[i+1]) for i in range(1, len(sections)-1, 2)]
    
    # Open the output file
    with open(output_path, 'w', encoding='utf-8') as outfile:
        if book_name:
            outfile.write(f"{book_name}\n")  # Write only the book name
        
        # Process the remaining sections (starting from the second section)
        # The second section in the input file is the first section of the book, so we use an offset of 1
        expected_section_number = 1  # The first section of the book is 1
        for section_number, section_content in sections[:]:
            # Check if the section number matches the expected sequence
            if int(section_number) == expected_section_number:
                # Check if the next section number is in this section due to pdf formatting issue.
                collapsed_section = section_content.find(f"<b>{int(section_number) + 1}</b>\n")
                if collapsed_section != -1:
                    # next section found. fix this section and add 
                    prev_sec = section_content[:collapsed_section]
                    combined_section = f"{section_number}\n{prev_sec}"
                    parsed_section = parse_section(combined_section)
                    if parsed_section:
                        outfile.write(','.join(parsed_section) + '\n')
                    # now fix collapsed section and add that too
                    next_sec = section_content[collapsed_section + 1 + len(f"<b>{int(section_number) + 1}</b>"):]
                    combined_section = f"{int(section_number) + 1}\n{next_sec}"
                    parsed_section = parse_section(combined_section)
                    if parsed_section:
                        outfile.write(','.join(parsed_section) + '\n')

                    expected_section_number += 2
                    continue

                # Combine the section number and content for parsing
                combined_section = f"{section_number}\n{section_content}"
                parsed_section = parse_section(combined_section)
                if parsed_section:
                    outfile.write(','.join(parsed_section) + '\n')
                # Increment the expected section number for the next iteration
                expected_section_number += 1
            else:
                # If the section number doesn't match, there can be 2 things. 
                # Case 1. The section number is at the end of the last section due to pdf formatting issue. we have already accounted 
                # for that above so this is  definitely case 2
                # Case 2. Its a number that is just part of section text. treat it as part of the current section's content
                # Append it to the current section's content without disrupting the structure
                if outfile.tell() > 0:  # Check if the file is not empty
                    outfile.seek(outfile.tell() - 1)  # Move the file pointer to the end of the last line
                    outfile.write(f"\n{section_number} {section_content}\n")

# Input and output file paths
input_file = 'extracted_text.txt'
output_file = 'book.csv'

# Convert the input file to the desired CSV format
convert_to_csv(input_file, output_file)

print(f"Conversion complete. Output saved to {output_file}")