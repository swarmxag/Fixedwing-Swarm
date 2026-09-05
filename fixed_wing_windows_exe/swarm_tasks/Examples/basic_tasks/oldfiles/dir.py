import os

file_name = "pos.csv"  # Specify the file name

# Construct the full path to the file in the current directory
file_path = os.path.join(os.getcwd(), file_name)

with open(file_path, 'w') as csvfile:
    # Your file handling code here
    pass  # Placeholder for your file handling code

