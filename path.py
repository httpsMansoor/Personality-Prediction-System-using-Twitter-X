import os
from pathlib import Path

# Add more possible locations
possible_paths = [
    Path(os.path.expanduser('~')) / '.cache' / 'huggingface' / 'hub',
    Path(os.path.expanduser('~')) / '.cache' / 'huggingface' / 'transformers',
    Path(os.path.expanduser('~')) / 'AppData' / 'Local' / 'huggingface',
    Path(os.getcwd()) / 'models'  # Local project directory
]

def search_model_files(path):
    if not path.exists():
        print(f"Directory not found: {path}")
        return
    
    print(f"\nSearching in: {path}")
    # Search for both bart-large-mnli and facebook/bart patterns
    patterns = ["*bart-large-mnli*", "*facebook*bart*", "*bart*mnli*"]
    
    found = False
    for pattern in patterns:
        for item in path.rglob(pattern):
            found = True
            print(f"- {item}")
            if item.is_file():
                print(f"  Size: {item.stat().st_size / 1024 / 1024:.2f} MB")
    
    if not found:
        print("No matching files found in this location.")

print("Searching for BART model files...")
for path in possible_paths:
    search_model_files(path)

# If no files found, provide instructions
print("\nIf no model files were found, you can download them using:")
print("from transformers import AutoModel")
print("model = AutoModel.from_pretrained('facebook/bart-large-mnli')")