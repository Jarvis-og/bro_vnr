# answer.py - Query RAG system and generate answer with Ollama LLM

import chromadb
from chromadb.config import Settings
import argparse
from sentence_transformers import SentenceTransformer
import subprocess

import time

def query_and_answer(question, db_path="./chroma_db", n_results=3, model="llama3.2:3b"):

    start = time.time()

    """Query ChromaDB and generate answer with Ollama"""
    
    print(f"→ Loading embedding model...")
    try:
        embedding_model = SentenceTransformer(
            './models/models--nomic-ai--nomic-embed-text-v1.5/snapshots/e5cf08aadaa33385f5990def41f7a23405aec398',
            trust_remote_code=True,
            device='cuda'
        )
        embedding_model.max_seq_length = 8192
        print("✓ Model loaded on CUDA")
    except Exception as e:
        print(f"⚠ CUDA not available, using CPU: {e}")
        embedding_model = SentenceTransformer(
            './models/models--nomic-ai--nomic-embed-text-v1.5/snapshots/e5cf08aadaa33385f5990def41f7a23405aec398',
            trust_remote_code=True
        )
    
    # Generate query embedding
    print(f"→ Generating query embedding...")
    query_embedding = embedding_model.encode([question], convert_to_numpy=True)[0]
    
    # Connect to ChromaDB
    print(f"→ Connecting to ChromaDB at {db_path}...")
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        collection = client.get_collection(name="documents")
        print(f"✓ Connected to collection with {collection.count()} documents")
    except Exception as e:
        print(f"✗ Error: Collection not found. Run setup.py first.")
        return False
    
    # Query collection
    print(f"→ Retrieving top {n_results} relevant chunks...")
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=n_results
    )
    
    if not results['documents'][0]:
        print("✗ No relevant documents found")
        return False
    
    # Build context from retrieved chunks
    contexts = []
    sources = []
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        similarity = 1 - distance
        contexts.append(f"[Source {i+1}] {doc}")
        sources.append({
            'source': metadata.get('source', 'Unknown'),
            'chunk': metadata.get('chunk_index', 'N/A'),
            'similarity': similarity
        })
    
    context = "\n\n".join(contexts)
    
    # Build prompt for LLM
    prompt = f"""You are a helpful AI assistant developed by students of the EEE department at VNR VJIET to assist with academic and technical queries.

        Answer the user's questions in short, limiting to the query based only on the provided context below.
        The context contains information from multiple sources including PDFs, Word documents, PowerPoint presentations, Excel sheets, and text files.
        Greet the user when they greet you.

        Answer the question if it is related to engineering branches:
        - computer science
        - mechanical
        - civil
        - electrical
        - electronics
        - auto mobile
        - chemistry
        - physics
        - mathematics

        If the answer is not found in the context or not related to engineering:
        "I don't know."

        If the query is from any different category like food, media and entertainment, sports, respond only with:
        "I don't know."
        
        If the user uses abusive or offensive language, respond with:
        "Please maintain a respectful tone."
        ---
        Context:
        {context}

        Question:
        {question}

        Answer:
    """
    
    print(f"→ Generating answer with {model}...")
    print("\n" + "="*80)
    print(f"QUESTION: {question}")
    print("="*80 + "\n")
    
    # Call Ollama
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"✗ Error running Ollama: {result.stderr}")
            return False
        
        answer = result.stdout.strip()
        print("ANSWER:")
        print("-" * 80)
        print(answer)
        print("\n" + "="*80)
        
        # Show sources
        print("\nSOURCES:")
        print("-" * 80)
        for i, src in enumerate(sources, 1):
            print(f"{i}. {src['source']} (chunk {src['chunk']}) - Similarity: {src['similarity']:.3f}")
        print("="*80 + "\n")

        end = time.time()

        print("\ntime taken to generate the answer =", end-start)
        
        return True

    except subprocess.TimeoutExpired:
        print("✗ Timeout: LLM took too long to respond")
        return False
    except FileNotFoundError:
        print("✗ Error: Ollama not found. Install with: curl -fsSL https://ollama.com/install.sh | sh")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query RAG system with LLM answer generation")
    parser.add_argument("question", help="Question to ask")
    parser.add_argument("--db", default="./chroma_db", help="Database path (default: ./chroma_db)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve (default: 3)")
    parser.add_argument("--model", default="qwen3:0.6b", help="Ollama model to use (default: llama3.2:3b)")
    
    args = parser.parse_args()
    
    success = query_and_answer(
        args.question,
        args.db,
        args.top_k,
        args.model
    )
    
    if not success:
        exit(1)
