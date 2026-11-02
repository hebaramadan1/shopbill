import os
import shutil
import traceback

# توجيه مسار الكاش ومكتبة التضمينات للبارتيشن D حصرياً لتجنب امتلاء قرص C نهائياً
os.environ["CHROMA_CACHE_DIR"] = "D:/shopbill_chroma_cache"
os.makedirs("D:/shopbill_chroma_cache", exist_ok=True)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
from parser import parse_invoice_pdf
import chromadb

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# تعريف تطبيق الـ FastAPI بصراحة
app = FastAPI(title="ShopBill Professional ChromaDB & Enterprise RAG Engine on Drive D")

# تفعيل CORS للاتصال مع الواجهة الأمامية
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "D:/shopbill_temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# توجيه قاعدة البيانات المتجهية ChromaDB حصرياً إلى البارتيشن D
VECTOR_DB_PATH = "D:/shopbill_vector_db"
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

print("Initializing Enterprise ChromaDB on Drive D...")
chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
collection = chroma_client.get_or_create_collection(name="shopbill_financial_docs")

# تهيئة عميل Groq مع ضبط المهلة الزمنية لمنع انقطاع الاتصال (Timeout)
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=30.0,
    max_retries=3
)

class ChatRequest(BaseModel):
    message: str
    context_data: str = ""

@app.get("/")
def read_root():
    return {"status": "ShopBill ChromaDB Engine on Drive D is running successfully! 🚀"}

@app.post("/api/extract-invoice")
async def extract_invoice(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        extracted_data = parse_invoice_pdf(file_path)
        doc_text = str(extracted_data)
        doc_id = f"invoice_{file.filename}_{os.path.getmtime(file_path)}"
        
        collection.add(
            documents=[doc_text],
            metadatas=[{"source": file.filename}],
            ids=[doc_id]
        )
        
        return {"success": True, "data": extracted_data, "message": "Document indexed successfully in ChromaDB on Drive D!"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/api/chat")
async def financial_chat(request: ChatRequest):
    try:
        search_results = collection.query(
            query_texts=[request.message],
            n_results=3
        )
        
        retrieved_docs = search_results.get("documents", [[]])[0]
        retrieved_sources = search_results.get("metadatas", [[]])[0]
        
        vector_context = "\n---\n".join(retrieved_docs) if retrieved_docs else "No historical records found."
        combined_context = f"ChromaDB Retrieved Records (from Drive D):\n{vector_context}\n\nAdditional Context:\n{request.context_data}"

        system_prompt = (
            "You are an expert financial assistant for ShopBill. "
            "Answer the user's question accurately using ONLY the provided financial context and stock records. "
            "If the information is missing, politely state that you don't have enough data. "
            "Always include source references (like invoice numbers or document names) when available."
        )

        user_prompt = f"{combined_context}\n\nUser Question: {request.message}"

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.1,
        )

        reply_text = chat_completion.choices[0].message.content
        return {"success": True, "reply": reply_text, "sources": retrieved_sources}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # تمرير الكائن app مباشرة لتفادي أي أخطاء في البحث النصي للـ Uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)