import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form

from controllers.faceRecog import face_verification
from controllers.uploadImg import upload
from mapFiles.nav_controller import router as nav_router
 
# from assistant.setup import setup_database
# from assistant.ingest import run_folder_ingestion
# from assistant.answer import query_and_answer
 
sys.path.append(os.path.join(os.path.dirname(__file__), "assistant"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# DB_PATH = "./assistant/chroma_db"
# DATA_PATH = "./assistant/data"

@app.post("/verify")
async def verify_face(file: UploadFile = File(...)):
    result = await face_verification(file)
    return result

@app.post("/admin/upload")
async def upload_photos(
    password: str = Form(...), 
    person_name: str = Form(...), 
    files: list[UploadFile] = File(...)
):
    response = await upload(password, person_name, files)
    return response

app.include_router(nav_router)

class ChatRequest(BaseModel):
    question: str
    model: str = "qwen2.5:0.5b"
    top_k: int = 5
 
 
class ChatResponse(BaseModel):
    answer: str
    success: bool
 
 
# @app.post("/setup")
# def setup():
#     try:
#         success = setup_database(db_path=DB_PATH)
#         if success:
#             return {"success": True, "message": "Database setup complete."}
#         else:
#             raise HTTPException(status_code=500, detail="Database setup failed.")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
 
 
# @app.post("/ingest")
# def ingest():
#     try:
#         run_folder_ingestion(folder_path=DATA_PATH, db_path=DB_PATH)
#         return {"success": True, "message": "Documents ingested successfully."}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
 
 
# @app.post("/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     answer = query_and_answer(
#         question=req.question,
#         db_path=DB_PATH,
#         n_results=req.top_k,
#         model=req.model,
#     )

#     if answer is None:
#         raise HTTPException(status_code=500, detail="Failed to generate answer.")

#     return ChatResponse(answer=answer, success=True)
 
 
@app.get("/health")
def health():
    return {"status": "ok"}
 