import tkinter as tk
import csv
import os
import re
from functools import partial
from PIL import Image, ImageTk

root = None
book_title = ""
title_widget = None
text_frame = None
text_widget = None
button_frame = None
image_frame = None
image_label = None
buttons = []
book_data = {}
read_head = "1"
fg_color = "black"
bg_color = "white"

class BookIndex:
    content = ""
    links = []
    img = ""

# book data is in this format:
# index, text_content, link_count, link1_index, link2_index, ... , image_filename
def load_data(file):

    full_path = os.path.dirname(__file__)
    data_path = os.path.join(full_path, "data", file)

    with open(data_path, mode ='r', encoding="utf-8") as file:
        data_set = csv.reader(file)
        for data in data_set:
            global book_title
            if book_title == "":
                book_title = data[0]
                continue
            book_data[data[0]] = BookIndex()
            book_data[data[0]].content = data[1]

            links = []
            for i in range(int(data[2])):
                links.append(data[3+i])
            book_data[data[0]].links = links.copy()
            book_data[data[0]].img = data[-1]

def resize_image(image, width):
    # Maintain aspect ratio
    original_width, original_height = image.size
    aspect_ratio = original_height / original_width
    new_height = int(width * aspect_ratio)
    if new_height > 500:
        aspect_ratio = original_width / original_height
        width = int(width * aspect_ratio)
        new_height = 500
    return image.resize((width, new_height), Image.LANCZOS)

def load_image(image_path, image_label, text_widget):
    full_path = os.path.realpath(__file__)
    img_path = os.path.dirname(full_path) + "\\data\\" + image_path

    try:
        image = Image.open(img_path)
        resized_image = resize_image(image, 600)
        photo = ImageTk.PhotoImage(resized_image)
        image_label.config(image=photo)
        image_label.image = photo

        # Adjust the text widget height based on the image height
        image_height = resized_image.size[1]
        total_height = 660  # Original window height
        text_widget_height = total_height - image_height
        text_widget.config(height=int(text_widget_height / 20))  # 20 is an approximate height of a text line in pixels

    except Exception as e:
        image_label.config(text=f"Failed to load image: {e}")

def save_game():
    full_path = os.path.dirname(__file__)
    game_file_path = os.path.join(full_path, "data", "game.sav")
    with open(game_file_path, "w", encoding="utf-8") as text_file:
        text_file.write(read_head)

def load_game():
    full_path = os.path.dirname(__file__)
    game_file_path = os.path.join(full_path, "data", "game.sav")
    with open(game_file_path, 'r', encoding='utf-8') as infile:
        section = infile.read()
    link_item(section)

def main():
    # load book data
    load_data("book.csv")
    
    # Create the main tkinter window
    global root
    root = tk.Tk()
    root.title(book_title)
    root.geometry("600x800")
    root.resizable(False, False)

    # Create a main frame to hold the text section and the buttons section
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

     # Create a frame for the title section (Top, Non-Scrollable)
    title_frame = tk.Frame(main_frame, bg="gray")
    title_frame.pack(fill=tk.X)

    # Add "Load" button to the left of the title
    load_button = tk.Button(title_frame, text="Load", font=("Impact", 12), command=load_game)
    load_button.pack(side=tk.LEFT, padx=10, pady=10)

    # Create the Text widget for displaying the title (Non-Scrollable)
    global title_widget
    title_widget = tk.Label(title_frame, text="Title Placeholder", font=("Impact", 16), 
                            bg=bg_color, fg=fg_color, padx=10, pady=10)
    title_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # Add "Save" button to the right of the title
    save_button = tk.Button(title_frame, text="Save", font=("Impact", 12), command=save_game)
    save_button.pack(side=tk.RIGHT, padx=10, pady=10)

    # Load and display a placeholder image
    global image_frame
    image_frame = tk.Frame(main_frame)
    image_frame.pack(fill=tk.X)
  
    # Create a frame for the text area (left side)
    global text_frame
    text_frame = tk.Frame(main_frame)
    text_frame.pack(fill=tk.BOTH, expand=True)

    # Create the Text widget for displaying text
    global text_widget
    text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Cascadia Mono", 12), bg=bg_color, fg=fg_color, padx=10, pady=0)
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
    text_widget.tag_config("table_tag", font=("Cascadia Mono", 12))

    # Create a frame for the buttons (bottom)
    global button_frame
    button_frame = tk.Frame(root, bg="gray")
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)
    button = tk.Button(button_frame, text="☀", command=switch_theme)
    button.pack(side=tk.RIGHT, padx=10, pady=10)

    link_item(read_head)

    # Run the application
    root.mainloop()

# link story item 
def link_item(index):
    # Reset text widget height
    text_widget.config(height=int(660 / 20))  # Reset to default height

    global image_label
    global text_frame
    
    # Check if the book item has an image
    if book_data[index].img:
        # If image_label doesn't exist, create it and pack the image_frame
        if image_label is None:
            image_label = tk.Label(image_frame)
            image_label.pack(fill=tk.X)  # Pack it to fill the width of the frame

        # Load the image into the label
        load_image(book_data[index].img, image_label, text_widget)

        # Ensure the image_frame is visible and packed above the text_frame
        image_frame.pack(fill=tk.X, before=text_frame)  # Pack above the text_frame
    else:
        # If no image, remove the image label if it exists
        if image_label:
            image_label.pack_forget()  # Remove the image from view
            image_label.destroy()  # Destroy the label
            image_label = None  # Nullify the reference

        # Hide the image_frame entirely (so it doesn't take up space)
        image_frame.pack_forget()  # Remove the frame from the layout

    # Update the title widget with the current index
    title_widget.config(text=index)
    global read_head
    read_head = index  # undate current read_head (for save/load)

    # Prepare the text widget for content display
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)

    # Define the patterns for bold, italic, and table text
    patterns = [
        (r"<b>(.*?)</b>", "bold_tag"),
        (r"<i>(.*?)</i>", "italic_tag"),
        (r"<tc>(.*?)</tc>", "combat_table_tag"),
        (r"<tm>(.*?)</tm>", "market_table_tag")
    ]

    # Track the current position in the text
    pos = 0

    while pos < len(book_data[index].content):
        next_match = None
        tag_name = None

        # Find the earliest match for any tag type
        for pattern, name in patterns:
            match = re.search(pattern, book_data[index].content[pos:], re.DOTALL)
            if match:
                if not next_match or match.start() < next_match.start():
                    next_match = match
                    tag_name = name
        
        if next_match:
            # Insert normal text before the matched tag
            normal_text = book_data[index].content[pos:pos + next_match.start()]
            text_widget.insert(tk.END, normal_text)

            if tag_name == "combat_table_tag":
                # Process table content
                table_text = next_match.group(1).strip()
                
                # Split table cells by lines
                table_cells = [line.strip() for line in table_text.split('\n') if line.strip()]
                
                # Break cells into rows of 4 items each
                rows = [table_cells[i:i+4] for i in range(0, len(table_cells), 4)]
                
                # Determine max column widths for alignment
                col_widths = [max(len(row[i]) for row in rows) for i in range(4)]
                
                # Insert table rows

                for idx, row in enumerate(rows):
                    formatted_row = ""
                    items = []
                    if idx == 0:
                        for i, col in enumerate(row):
                            items.append(col[3:-4].rstrip('\t').ljust(col_widths[i]))
                        formatted_row = " ".join(items)
                        text_widget.insert(tk.END, '\n' + formatted_row + '\n', "italic_tag")
                    else:
                        for j, col in enumerate(row):
                            if j == 0:
                                text_widget.insert(tk.END, col.ljust(col_widths[j]), "bold_tag")
                            else:
                                items.append(col.ljust(col_widths[j]))

                        formatted_row = "  ".join(items)
                        text_widget.insert(tk.END, formatted_row + '\n', "table_tag")
            elif tag_name == "market_table_tag":
                # Process table content
                table_text = next_match.group(1).strip()
                
                # Split table cells by lines
                table_cells = [line.strip() for line in table_text.split('\n') if line.strip()]
                
                # Break cells into rows of 4 items each
                rows = [table_cells[i:i+3] for i in range(0, len(table_cells), 3)]
                
                # Determine max column widths for alignment
                col_widths = [max(len(row[i]) for row in rows) for i in range(3)]
                
                # Insert table rows

                for idx, row in enumerate(rows):
                    formatted_row = ""
                    items = []
                    if idx == 0:
                        for i, col in enumerate(row):
                            items.append(col[3:-4].rstrip('\t').ljust(col_widths[i]))
                        formatted_row = " ".join(items)
                        text_widget.insert(tk.END, '\n' + formatted_row + '\n', "italic_tag")
                    else:
                        for j, col in enumerate(row):
                            if j == 0:
                                text_widget.insert(tk.END, col[3:-4].rstrip('\t').ljust(col_widths[j]), "bold_tag")
                            else:
                                items.append(col.rstrip('\t').ljust(col_widths[j]))

                        formatted_row = " ".join(items)
                        text_widget.insert(tk.END, formatted_row + '\n', "table_tag")          
            else:
                # Insert formatted text for bold or italic
                formatted_text = next_match.group(1)
                text_widget.insert(tk.END, formatted_text, tag_name)

            # Move the position pointer past this tag
            pos += next_match.end()
        else:
            # No more tags, insert the rest of the text
            text_widget.insert(tk.END, book_data[index].content[pos:])
            break

    text_widget.config(state=tk.DISABLED)  # Disable editing

    # Clear any previously created buttons
    for button in buttons:
        button.destroy()

    # Show buttons for links related to the current index
    show_buttons(book_data[index].links)

# show a button for each item. Items is a list containing indexes
def show_buttons(items):
    count = len(items)
    # can hold max 12 buttons
    # Adjust for best fit buttons (Optimal specs: width 5 chars, pad= 10 px)
    final_width = 5 # each char takes 15px approx. so 75
    final_pad = 10
    optimal_space = count * 75 + (count - 1) * 10
    if optimal_space > 615:
        final_pad = 0
        while final_pad < 2:
            space = 615 - (final_width * count * 15)
            final_pad = min(int(space / (count - 1)), 10)
            if final_pad < 2:
                final_width -= 1

    # Create some buttons and add them to the button_frame
    for item in items:
        button = tk.Button(button_frame, text=item, width=final_width, command=partial(link_item, item), font=("Impact", 12))
        button.pack(side=tk.LEFT, padx=final_pad, pady=10)
        buttons.append(button)


def switch_theme():
    global fg_color
    global bg_color

    temp = fg_color
    fg_color = bg_color
    bg_color = temp

    title_widget.config(bg=bg_color, fg=fg_color)
    text_widget.config(bg=bg_color, fg=fg_color)

if __name__ == "__main__":
    main()
