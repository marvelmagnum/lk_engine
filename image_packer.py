import tkinter as tk
from PIL import Image, ImageTk
import os
import csv

book_title = ""
book_data = {}

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

def main():
    root = tk.Tk()
    root.title("JPEG Image Viewer")
    root.resizable(False, False)

    # Store PhotoImage objects in a list to prevent garbage collection
    photo_references = []

    # Load all images from the folder
    full_path = os.path.realpath(__file__)
    folder_path = os.path.dirname(full_path) + "\\data\\"

    # List of image filenames
    image_files = ["img1.jpeg", "img2.jpeg"]  # Add more filenames as needed

    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)
        try:
            image = Image.open(image_path)
            image = resize_image(image, 600)
            photo = ImageTk.PhotoImage(image)
            photo_references.append(photo)  # Store the reference
        except Exception as e:
            print(f"Error loading image {image_file}: {e}")

    # Create a label to display the image
    label = tk.Label(root)
    label.pack()

    # Index to track the current image
    current_index = 0

    def show_next_image():
        # Clear the textbox
        textbox.delete(0, tk.END)

        nonlocal current_index
        if photo_references:
            if current_index < len(photo_references):
                # Update the label with the current image
                label.config(image=photo_references[current_index])
                current_index += 1

                # Update the image count label
                image_count_label.config(text=f"{current_index}/{len(photo_references)}")

                # If this is the last image, change the button text to "Quit"
                if current_index == len(photo_references):
                    next_button.config(text="Quit", command=root.destroy)
        else:
            print("No images to display.")

    # Create a frame to group the textbox and button
    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)  # Add some padding

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
        width=6  # Number of characters
    )
    textbox.pack(side=tk.LEFT, padx=5)  # Place the textbox to the left

    # Create a button to show the next image
    next_button = tk.Button(control_frame, text="Next", command=show_next_image)
    next_button.pack(side=tk.LEFT)  # Place the button to the right of the textbox.pack()

    # Show the first image initially
    show_next_image()

    root.mainloop()

if __name__ == "__main__":
    main()