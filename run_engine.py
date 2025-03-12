import tkinter as tk
import textwrap
import csv
import os
import re
from functools import partial

root = ""
book_title = ""
title_widget = None
text_widget = None
buttons = []
book_data = {}
read_head = "1"

class BookIndex:
    content = ""
    links = []
    img = ""

# book data is in this format:
# index, text_content, link_count, link1_index, link2_index, ... , image_filename
def load_data(file):

    full_path = os.path.realpath(__file__)
    data_path = os.path.dirname(full_path) + "\\data\\" + file
    with open(data_path, mode ='r', encoding="utf-8") as file:
        data_set = csv.reader(file)
        for data in data_set:
            global book_title
            if book_title == "":
                book_title = data[0]
                continue
            entry = BookIndex()
            entry.content = data[1]
            for i in range(int(data[2])):
                entry.links.append(data[3+i])
            entry.img = data[-1]
            book_data[data[0]] = entry

def main():
    # load book data
    load_data("vob.txt")
    
    # Create the main tkinter window
    root = tk.Tk()
    root.title(book_title)
    root.geometry("600x800")
    root.resizable(False, False)

    # Create a main frame to hold the text section and the buttons section
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

     # Create a frame for the title section (Top, Non-Scrollable)
    title_frame = tk.Frame(main_frame, bg="black")
    title_frame.pack(fill=tk.X)

    # Create the Text widget for displaying the title (Non-Scrollable)
    global title_widget
    title_widget = tk.Label(title_frame, text="Title Placeholder", font=("Cascadia Mono", 14, "bold"), 
                            bg="white", fg="black", padx=10, pady=10)
    title_widget.pack(fill=tk.X)

    # Create a frame for the text area (left side)
    text_frame = tk.Frame(main_frame)
    text_frame.pack(fill=tk.BOTH, expand=True)

    # Create the Text widget for displaying text
    global text_widget
    text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Cascadia Mono", 12), bg="white", fg="black", padx=10, pady=10)
    text_widget.grid(row=0, column=0, sticky="nsew")

    # Make sure the text_frame resizes properly
    text_frame.grid_rowconfigure(0, weight=1)
    text_frame.grid_columnconfigure(0, weight=1)

    # Create a Scrollbar and attach it to the Text widget
    scrollbar = tk.Scrollbar(text_frame, command=text_widget.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    text_widget.config(yscrollcommand=scrollbar.set)
    text_widget.tag_config("bold_tag", font=("Cascadia Mono", 12, "bold"))
    text_widget.tag_config("italic_tag", font=("Cascadia Mono", 12, "italic"))

    link_item(read_head)
    #show_buttons([214, 45, 654])

    # Run the application
    root.mainloop()

# link story item 
def link_item(index):
    # Update the title widget
    title_widget.config(text=index)

    # # Insert the justified text into the Text widget
    # text_widget.insert(tk.END, book_data[index].content)
    
    patterns = [
        (r"<b>(.*?)</b>", "bold_tag"),
        (r"<i>(.*?)</i>", "italic_tag")
    ]
    pos = 0

    while pos < len(book_data[index].content):
        next_tag = None
        next_match = None
        tag_name = None

        # Find the earliest match for any tag type
        for pattern, name in patterns:
            match = re.search(pattern, book_data[index].content[pos:])
            if match:
                if not next_match or match.start() < next_match.start():
                    next_match = match
                    next_tag = pattern
                    tag_name = name

        if next_match:
            # Insert text before the tag
            normal_text = book_data[index].content[pos:pos + next_match.start()]
            text_widget.insert(tk.END, normal_text)

            # Insert the formatted text with the appropriate tag
            formatted_text = next_match.group(1)
            text_widget.insert(tk.END, formatted_text, tag_name)

            # Move the position pointer past this tag
            pos += next_match.end()
        else:
            # No more tags, insert the rest of the text
            text_widget.insert(tk.END, book_data[index].content[pos:])
            break

    text_widget.config(state=tk.DISABLED)  # Disable editing

    for button in buttons:
        button.destroy()

    show_buttons(book_data[index].links)

# show a button for each item. Items is a list containing indexes
def show_buttons(items):
    count = len(items)

    # Create a frame for the buttons (bottom)
    button_frame = tk.Frame(root, bg="gray")
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Create some buttons and add them to the button_frame
    for item in items:
        button = tk.Button(button_frame, text=item, width=5, command=partial(link_item, item), font=("Impact", 12))
        button.pack(side=tk.LEFT, padx=10, pady=10)
        buttons.append(button)


if __name__ == "__main__":
    main()
