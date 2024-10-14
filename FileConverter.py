from PIL import Image
import pillow_heif
from PyPDF2 import PdfReader, PdfWriter
import os
import random
import string
import subprocess

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
subfolder_name = "Output"
subfolder_path = os.path.join(script_dir, subfolder_name)
os.makedirs(subfolder_path, exist_ok=True)

# Conversion functions
def convert_image(input_file, output_file, output_format):
    pillow_heif.register_heif_opener()
    img = Image.open(input_file)
    
    if output_format.upper() == "JPG":
        target_format = "JPEG"
    else:
        target_format = output_format.upper()

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    img.save(os.path.join(subfolder_path, output_file), format=target_format)

def convert_images(input_files, output_formats):
    for i, input_file in enumerate(input_files):
        output_format = output_formats[i]
        random_suffix = ''.join(random.choice(string.digits) for _ in range(3))
        input_filename = os.path.basename(input_file)
        output_file = f"{random_suffix}_{input_filename.rsplit('.', 1)[0]}.{output_format.lower()}"
        convert_image(input_file, output_file, output_format)

# PDF insertion function
def insert_pdf_page(writer, insert_pdf, page_number):
    reader_insert = PdfReader(insert_pdf)
    
    # Temporarily store current pages in writer
    original_pages = writer.pages[:page_number]  # Pages before the insertion point
    remaining_pages = writer.pages[page_number:]  # Pages after the insertion point
    
    # Add the pages from original_pdf before the insertion point
    new_writer = PdfWriter()
    for page in original_pages:
        new_writer.add_page(page)

    # Insert the new pages from the insert_pdf
    for page in reader_insert.pages:
        new_writer.add_page(page)

    # Add the remaining pages from the original writer
    for page in remaining_pages:
        new_writer.add_page(page)

    return new_writer

# Image mode function
def image_mode():
    input_files = []
    output_formats = []
    count = 1

    print("Supported filetypes are PNG, JPG, HEIF. Please write the file path of the file you wish to convert, followed by the desired output format.")
    
    while True:
        input_file = input(f"File Path #{count}: ").strip()
        if input_file.lower() == "done" or input_file == "":
            break
        input_files.append(input_file)

        output_format = input(f"Output Format #{count}: ").strip().upper()
        if output_format.lower() == "done" or output_format == "":
            break
        output_formats.append(output_format)
        
        count += 1

    if os.access(subfolder_path, os.W_OK):
        print(f"Write access to {subfolder_path} is granted.")
    else:
        print(f"No write access to {subfolder_path}.")
    
    print("Converting...")
    convert_images(input_files, output_formats)
    print(f"Converted Successfully! Files are saved in {subfolder_path}")

# PDF mode function
def pdf_mode():
    input_files = []
    page_indexes = []
    count = 1

    print("Please enter the file path of your base file")
    base_pdf_path = input().strip()  # Strip spaces from base file path

    while True:
        input_file = input(f"File Path #{count}: ").strip()  # Strip spaces from input file paths
        if input_file.lower() == "done" or input_file == "":
            break
        input_files.append(input_file)

        page_number = input("Merge to page (enter a number or leave blank for end): ").strip()  # Strip spaces
        if page_number == "":
            page_indexes.append(-1)  # -1 signifies appending at the end
        else:
            page_indexes.append(int(page_number))

        count += 1

    writer = PdfWriter()

    # First, add the base PDF pages to the writer
    base_reader = PdfReader(base_pdf_path)
    for page in base_reader.pages:
        writer.add_page(page)

    # Insert pages from other PDFs at specified positions
    for i, input_file in enumerate(input_files):
        page_index = page_indexes[i]
        
        if page_index == -1:  # Append at the end if no page specified
            page_index = len(writer.pages)
        
        writer = insert_pdf_page(writer, input_file, page_index)

    # Save the merged PDF
    random_suffix = ''.join(random.choice(string.digits) for _ in range(3))
    output_pdf_path = os.path.join(subfolder_path, str(random_suffix) + os.path.basename(base_pdf_path))
    with open(output_pdf_path, 'wb') as output_pdf:
        writer.write(output_pdf)

    print(f"Merging Successful! Output file path is: {output_pdf_path}")

# Main program
print("Welcome to the image/pdf conversion tool. Type 'PDF' for PDF mode or press enter for image mode.")
user_input = input("PDF or IMG: ").strip().upper()

if user_input == "PDF":
    pdf_mode()
else:
    image_mode()

# Open the output folder with subprocess to handle paths safely
if os.access(subfolder_path, os.R_OK):
    subprocess.Popen(["open", subfolder_path])  # macOS specific

print("Thanks for using! To convert more files, type 'y', otherwise enter.")
user_input = input().strip().lower()
if user_input == "y":
    print("Welcome to the image/pdf conversion tool. Type 'PDF' for PDF mode or press enter for image mode.")
    user_input = input("PDF or IMG: ").strip().upper()
    if user_input == "PDF":
        pdf_mode()
    else:
        image_mode()