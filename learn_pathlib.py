from pathlib import Path

r = Path (r"artifact\ikram Hashmi.docx")
# we can convert a relative path to absolute Path using:
print(r.resolve())
# Output: D:\projects\Resume-filtering-Agent\artifact\Resume.pdf

# we can get the file type(extention) using:
print(r.suffix)
# Output: .pdf

# we can get all the file extensions(using suffixes) using:
print(r.suffixes)  
# Output: ['.pdf']

# we can get the file name using:
print(r.name)
# Output: Resume.pdf

# we can check if the path exists using:
print(r.exists())
# Output: True

# we can check if it's a file using:
print(r.is_file())
# Output: True

# we can check if it's a directory using:
print(r.is_dir())
# Output: False

# we can get the parent directory using:
print(r.parent)
# Output: artifact