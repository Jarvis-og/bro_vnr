"""
ingest.py - Multi-format folder ingestion (PDF, DOCX, XLSX, MD, TXT)
"""
import os
import pandas as pd
from docx import Document
from pypdf import PdfReader
import chromadb
from sentence_transformers import SentenceTransformer

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif ext == '.docx':
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            text = df.to_string()
        elif ext in ['.md', '.txt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        return text
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def run_folder_ingestion(folder_path="./data", db_path="./chroma_db"):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created {folder_path} folder. Add your files there!")
        return

    # Load Model (CPU to save VRAM for later)
    model = SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', trust_remote_code=True, device='cpu')
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="documents")

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        print(f"→ Processing {filename}...")
        
        raw_text = extract_text(file_path)
        if raw_text:
            # Simple chunking logic (can be refined)
            chunks = [raw_text[i:i+1000] for i in range(0, len(raw_text), 900)]
            embeddings = model.encode(chunks)
            
            ids = [f"{filename}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": filename} for _ in range(len(chunks))]
            
            collection.add(ids=ids, embeddings=embeddings.tolist(), documents=chunks, metadatas=metadatas)
            print(f"✓ Ingested {filename}")

if __name__ == "__main__":
    run_folder_ingestion()
