import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import csv

book_title = ""
book_data = {}
data_file_name = "book.csv"

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

def validate_input(new_value):
    # Allow only positive numbers (including empty input for backspace)
    if new_value == "":
        return True
    try:
        value = int(new_value)
        if value >= 0:
            return True
        else:
            return False
    except ValueError:
        return False

def image_viewer(root):
    full_path = os.path.realpath(__file__)
    folder_path = os.path.dirname(full_path) + "\\data"

    images = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg"))]
    current_index = 0
    
    # Check if there are no jpeg images in the folder
    if not images:
        print("No JPEG images found in the folder.")
        root.quit()

    photo_references = []
    for img in images:
        image_path = folder_path + "\\" + img
        try:
            image = Image.open(image_path)
            image = resize_image(image, 600)
            photo = ImageTk.PhotoImage(image)
            photo_references.append((photo, img))  # Store the reference
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")

    # Create a label to display the image
    label = tk.Label(root)
    label.pack()

    # Index to track the current image
    current_index = 0

    def save_img_link():
        # Print the contents of the textbox to the console
        img_link = textbox.get()
        if img_link in book_data.keys():
            book_data[img_link].img = photo_references[current_index-1][1]
        
        # Clear the textbox
        textbox.delete(0, tk.END)

        if current_index == len(photo_references):
            # Write the data file and quit program
            full_path = os.path.realpath(__file__)
            data_path = os.path.dirname(full_path) + "\\data\\" + data_file_name
            with open(data_path, 'w', encoding='utf-8') as outfile:
                outfile.write(book_title + '\n')
                for data in book_data:
                    entry = data + ',"' + book_data[data].content + '",' + str(len(book_data[data].links))
                    for link in book_data[data].links:
                        entry += ',' + link
                    entry += ',"' + book_data[data].img + '"'
                    outfile.write(entry + '\n')
            root.destroy()
        else:
            show_next_image()

    def show_next_image():
        nonlocal current_index
        if photo_references:
            if current_index < len(photo_references):
                # Update the label with the current image
                label.config(image=photo_references[current_index][0])
                current_index += 1

                # Update the image count label
                image_count_label.config(text=f"{current_index}/{len(photo_references)}")

                # If this is the last image, change the button text to "Quit"
                if current_index == len(photo_references):
                    next_button.config(text="Quit")
        else:
            print("No images to display.")

    # Create a frame to group the image name label and control_frame
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)  # Place at the bottom

    # Add a label to display the image name at the bottom left
    image_name_label = tk.Label(bottom_frame, text=f"{photo_references[current_index][1]}", font=("Arial", 12), anchor="w")
    image_name_label.pack(side=tk.LEFT, padx=5)  # Place on the left side of the bottom_frame

    # Create a frame to group the image count label, textbox, and button
    control_frame = tk.Frame(bottom_frame)
    control_frame.pack(side=tk.RIGHT, padx=5)  # Place on the right side of the bottom_frame

    # Add a label to show the image count
    image_count_label = tk.Label(control_frame, text=f"0/{len(photo_references)}", font=("Arial", 12))
    image_count_label.pack(side=tk.LEFT, padx=5)  # Place the label to the left

    # Add a text input box with validation
    validate_cmd = root.register(validate_input)  # Register the validation function
    textbox = tk.Entry(
        control_frame,
        validate="key",
        validatecommand=(validate_cmd, "%P"),
        justify="center",  # Center-align the text
        font=("Impact", 12),  # Set font to Impact with size 12
        width=10  # Reduce the size of the textbox (default is typically 20 characters)
    )
    textbox.pack(side=tk.LEFT, padx=5)  # Place the textbox to the right of the label

    # Create a button to show the next image
    next_button = tk.Button(control_frame, text="Next", command=show_next_image)
    next_button.pack(side=tk.LEFT)  # Place the button to the right of the textbox

    # Show the first image initially
    show_next_image()

def main():
    root = tk.Tk()
    root.title("JPEG Image Viewer")
    root.resizable(False, False)

    load_data(data_file_name)

    # Initialize ImageViewer with the selected folder
    image_viewer(root)
        
    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()