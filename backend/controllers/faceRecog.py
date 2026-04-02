import os
import cv2
import numpy as np
from deepface import DeepFace
from utils.enhance_image import enhance_image

# Global variables to store fingerprints
KNOWN_EMBEDDINGS = []
KNOWN_NAMES = []
DB_PATH = "./my_db"
MODEL_NAME = "VGG-Face" # You can also use 'Facenet' or 'OpenFace'

def precompute_db():
    """Scans the folder once and stores 'fingerprints' (embeddings) in RAM."""
    global KNOWN_EMBEDDINGS, KNOWN_NAMES
    
    temp_embeddings = []
    temp_names = []

    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)
        print(f"Created directory: {DB_PATH}")
        return

    print("Precomputing DeepFace embeddings...")
    
    files = [f for f in os.listdir(DB_PATH) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    for file in files:
        img_path = os.path.join(DB_PATH, file)
        try:
            # Extract the numerical representation (embedding)
            # enforce_detection=False prevents crashing if a photo has a side-profile or shadow
            results = DeepFace.represent(img_path=img_path, model_name=MODEL_NAME, enforce_detection=False)
            
            if results:
                embedding = results[0]["embedding"]
                temp_embeddings.append(embedding)
                # Save name: 'aryan_01.jpg' -> 'aryan'
                temp_names.append(file.split('_')[0])
                print(f"Loaded: {file}")
                
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    # Convert to NumPy for high-speed vector math
    if temp_embeddings:
        KNOWN_EMBEDDINGS = np.array(temp_embeddings)
        KNOWN_NAMES = temp_names
        print(f"✅ DeepFace: Loaded {len(KNOWN_NAMES)} faces into RAM.")
    else:
        print("⚠️ No faces found in database.")

# Run once when the backend starts
precompute_db()

async def face_verification(file):
    print(f"Received file: {file.filename}")
    temp_path = "temp_frame.jpg"

    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    frame = cv2.imread(temp_path)
    if frame is None:
        return {"success": False, "error": "Could not read uploaded image"}

    enhanced_frame = enhance_image(frame)

    try:
        # 1. Get embedding of current frame (only 1 AI run)
        target_obj = DeepFace.represent(img_path=enhanced_frame, model_name=MODEL_NAME, enforce_detection=False)
        
        if not target_obj:
            return {"success": False, "name": "No face detected"}
            
        target_emb = np.array(target_obj[0]["embedding"])

        # 2. VECTOR MATH (Cosine Similarity)
        # This compares the new face against all stored faces in RAM instantly
        dot_product = np.dot(KNOWN_EMBEDDINGS, target_emb)
        norms = np.linalg.norm(KNOWN_EMBEDDINGS, axis=1) * np.linalg.norm(target_emb)
        similarities = dot_product / norms
        
        # 3. Find the best match
        best_idx = np.argmax(similarities)
        high_score = similarities[best_idx]

        print(f"Top Match: {KNOWN_NAMES[best_idx]} with Score: {high_score:.4f}")

        # 4. Threshold Logic
        # VGG-Face is accurate above 0.70. If it's below this, it's a 'Wrong Person' guess.
        if high_score > 0.70: 
            return {"success": True, "faces": [{"name": KNOWN_NAMES[best_idx], "confidence": float(high_score)}]}
        
        return {"success": False, "faces": [], "message": "Unknown person"}

    except Exception as e:
        print(f"DeepFace Error: {e}")
        return {"success": False, "error": str(e)}
