import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
from parser import parse_invoice_pdf

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

app = FastAPI(title="ShopBill AI Document Extraction & RAG Engine")

# تفعيل CORS للاتصال مع Frontend (Vite / React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# تهيئة عميل Groq باستخدام المفتاح البيئي
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    context_data: str = ""  # بيانات الفواتير أو المخزون المرفقة للـ RAG

@app.get("/")
def read_root():
    return {"status": "ShopBill AI Engine is running successfully! 🚀"}

@app.post("/api/extract-invoice")
async def extract_invoice(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        extracted_data = parse_invoice_pdf(file_path)
        return {"success": True, "data": extracted_data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/api/chat")
async def financial_chat(request: ChatRequest):
    try:
        # إعداد نظام التوجيه للذكاء الاصطناعي (System Prompt) لضمان الدقة المالية ومنع الهلوسة
        system_prompt = (
            "You are an expert financial assistant for ShopBill. "
            "Answer the user's question accurately using ONLY the provided financial context and stock records. "
            "If the information is missing, politely state that you don't have enough data. "
            "Always include source references (like invoice numbers or document names) when available."
        )

        user_prompt = f"Financial Context:\n{request.context_data}\n\nUser Question: {request.message}"

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-70b-8192",  # نموذج Groq السريع والقوي جداً
            temperature=0.1,         # نسبة هلوسة منخفضة جداً للحسابات والبيانات المالية
        )

        reply_text = chat_completion.choices[0].message.content
        return {"success": True, "reply": reply_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)