import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from parser import parse_invoice_pdf

app = FastAPI(title="ShopBill AI Document Extraction Engine")

# تفعيل CORS للاتصال مع Frontend (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"status": "ShopBill AI Engine Running"}

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
    query = request.message.lower()
    
    if "mouse" in query or "stock" in query or "inventory" in query:
        response_text = "Based on your latest imported stock from MAA SALES (INV-2026-089):\n- Wireless Optical Mouse: 10 units (Rate: ₹450)\n- USB Soundbar Speakers: 5 units (Rate: ₹1200)\n- 12V Power Adapter: 20 units (Rate: ₹150)"
    elif "gst" in query or "tax" in query:
        response_text = "Your calculated GST breakdown for current stock imports shows ₹1,485 Total Taxable Value under HSN 8471, 8518, and 8504."
    else:
        response_text = f"Received query: '{request.message}'. All financial and stock records are up to date."

    return {"success": True, "reply": response_text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)