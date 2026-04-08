from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form

from controllers.faceRecog import face_verification
from controllers.uploadImg import upload
from mapFiles.nav_controller import router as nav_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

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
