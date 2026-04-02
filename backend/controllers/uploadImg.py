import os
import shutil
from fastapi import HTTPException

from controllers.faceRecog import precompute_db

DB_PATH = "./my_db" 
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

ADMIN_PASSWORD = "password"

async def upload(password, person_name, files):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid Admin Password")

    clean_name = person_name.strip()

    saved_count = 0
    try:
        for i, file in enumerate(files, 1):
            filename = f"{clean_name}_{i:02d}.jpg"
            file_path = os.path.join(DB_PATH, filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_count += 1

        # Optional: If you are using a Vector DB or InsightFace, 
        # call your sync function here to update the 'known faces' in RAM
        # sync_database() 
        
        precompute_db()

        return {
            "success": True, 
            "message": f"Successfully saved {saved_count} photos for {person_name}."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving files: {str(e)}")
    
