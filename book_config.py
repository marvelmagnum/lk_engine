BOOK_INDEX = "b1"

# To extract a new book:
# 1. Set BOOK_INDEX to the new book's index.
# 2. Run the book_extractor.py script to extract images and text for the new book. 
#    This will create a data folder with extracted images and an output folder with a 
#    text file of the raw text content.
# 3. Next run the bookdata_builder.py script to build the formatted book data file using the extracted text content.
# 4. Finally, its time to run the image_packer.py script to index and pack the images into the book data.
#    a) To generate the image index data set interactive mode to true. This will create the image data file if it does
#    not exist. Then open the image viewer to allow you to manually map the iamges. It will then update the image 
#    data file with the correct mappings and then pack the images into the book data file.
#    b) If an indexed image data file already exists, then the interactive mode can be set to false. The script will 
#    use the image data file (images.csv) to load the mappings and pack the images into the book data file.

