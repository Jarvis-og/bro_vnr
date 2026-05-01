# import os
# import cv2
# import numpy as np
# from insightface.app import FaceAnalysis

# # 1. Initialize InsightFace once (Global)
# # Force ONLY the CPU provider to avoid the CUDA DLL search
# face_app = FaceAnalysis(
#     name='buffalo_l', 
#     providers=['CPUExecutionProvider'] # Remove 'CUDAExecutionProvider' here
# )
# # ctx_id=-1 explicitly tells it to stay off the GPU
# face_app.prepare(ctx_id=-1, det_size=(640, 640))

# # In-memory database
# KNOWN_EMBEDDINGS = []
# KNOWN_NAMES = []
# DB_PATH = "./my_db"

# def precompute_db():
#     """Scans the folder once and stores 'fingerprints' in RAM."""
#     global KNOWN_EMBEDDINGS, KNOWN_NAMES
#     KNOWN_EMBEDDINGS = []
#     KNOWN_NAMES = []

#     if not os.path.exists(DB_PATH):
#         os.makedirs(DB_PATH)
#         return

#     for file in os.listdir(DB_PATH):
#         if file.lower().endswith(('.jpg', '.jpeg', '.png')):
#             img_path = os.path.join(DB_PATH, file)
#             img = cv2.imread(img_path)
#             if img is not None:
#                 faces = face_app.get(img)
#                 if faces:
#                     # We take the first face found in the image
#                     KNOWN_EMBEDDINGS.append(faces[0].normed_embedding)
#                     # Get name from filename (e.g., 'aryan_01.jpg' -> 'aryan')
#                     KNOWN_NAMES.append(file.split('_')[0])
    
#     # Convert list to a fast NumPy matrix for instant math
#     if KNOWN_EMBEDDINGS:
#         KNOWN_EMBEDDINGS = np.array(KNOWN_EMBEDDINGS)
#     print(f"✅ InsightFace: Loaded {len(KNOWN_NAMES)} faces into RAM.")

# # Run precompute once on startup
# # precompute_db()

# async def face_verification(file):
#     # 2. Read and Enhance
#     content = await file.read()
#     nparr = np.frombuffer(content, np.uint8)
#     frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
#     if frame is None:
#         return {"success": False, "error": "Invalid Image"}

#     # Use your existing enhancement function
#     from utils.enhance_image import enhance_image
#     enhanced_frame = enhance_image(frame)

#     try:
#         # 3. Detect and Represent the current frame
#         faces = face_app.get(enhanced_frame)
        
#         if not faces:
#             print("No face detected")
#             return {"success": False, "faces": []}

#         # Take the embedding of the detected face
#         target_emb = faces[0].normed_embedding

#         # 4. Compare using Cosine Similarity (Vector Math)
#         # This is the 'Optimization'—no disk reading here!
#         if len(KNOWN_NAMES) > 0:
#             # Dot product of normalized vectors = Cosine Similarity
#             similarities = np.dot(KNOWN_EMBEDDINGS, target_emb)
#             best_idx = np.argmax(similarities)
#             score = similarities[best_idx]

#             # Threshold for InsightFace (typically 0.4 to 0.5)
#             if score > 0.45:
#                 name = KNOWN_NAMES[best_idx]
#                 print(f"Match found: {name} ({score:.2f})")
#                 return {"success": True, "faces": [{"name": name, "confidence": float(score)}]}

#         print("No match found")
#         return {"success": False, "faces": []}

#     except Exception as e:
#         print(f"InsightFace Error: {e}")
#         return {"success": False, "error": str(e)}
    
