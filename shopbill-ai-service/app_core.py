import os
import shutil
import traceback
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from parser import parse_invoice_pdf

app = FastAPI(title="ShopBill AI RAG Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

VECTOR_DB_PATH = "D:/shopbill_vector_db"
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

try:
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = chroma_client.get_or_create_collection(name="shopbill_invoices")
    print(f"ChromaDB successfully initialized at: {VECTOR_DB_PATH}")
except Exception as e:
    print(f"Error initializing ChromaDB: {e}")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"status": "ShopBill AI Backend is running successfully on Drive D"}

@app.post("/api/extract-invoice")
async def extract_invoice(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        extracted_data = parse_invoice_pdf(file_path)
        if not extracted_data or not extracted_data.get("items"):
            raise HTTPException(status_code=422, detail="Could not extract any valid items from the invoice PDF.")
            
        doc_text = f"File Name: {file.filename}, Supplier: {extracted_data.get('supplier_name')}, Invoice No: {extracted_data.get('invoice_no')}, Items: {str(extracted_data.get('items'))}"
        doc_id = f"invoice_{file.filename}_{os.path.getmtime(file_path)}"
        
        try:
            collection.delete(ids=[doc_id])
        except Exception:
            pass

        collection.add(
            documents=[doc_text],
            metadatas=[{"source": file.filename, "filename": file.filename}],
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
async def chat_with_rag(request: ChatRequest):
    try:
        user_query = request.message
        
        invoice_keywords = [
            "invoice", "bill", "supplier", "item", "quantity", "rate", "amount", 
            "brush", "mop", "hsn", "stock", "price", "product",
            "चालान", "बिल", "सामान", "स्टॉक", "मूल्य"
        ]
        
        invoice_match = re.search(r'\b\d+\b', user_query)
        has_keyword = any(keyword in user_query.lower() for keyword in invoice_keywords)
        is_hindi = any('\u0900' <= char <= '\u097F' for char in user_query)

        if not invoice_match and not has_keyword:
            if is_hindi:
                response_message = "क्षमा करें, यह प्रश्न अपलोड किए गए चालान अभिलेखों से बाहर है। कृपया चालान विवरण, इन्वेंट्री या आपूर्तिकर्ता के बारे में पूछें।"
            else:
                response_message = "Sorry, this question is outside the scope of the uploaded invoice records. Please ask about invoice details, inventory, or registered suppliers."
            
            return {
                "success": True,
                "response": response_message,
                "sources": []
            }

        results = None
        if invoice_match:
            inv_num = invoice_match.group()
            target_filename = f"{inv_num}.pdf"
            
            try:
                results = collection.query(
                    query_texts=[user_query],
                    where={"filename": target_filename},
                    n_results=1
                )
            except Exception:
                results = None

        if not results or not results.get("documents") or not results["documents"][0]:
            results = collection.query(
                query_texts=[user_query],
                n_results=1
            )
        
        context_docs = []
        if results and "documents" in results and results["documents"] and results["documents"][0]:
            context_docs = results["documents"][0]
            
        metadatas = []
        if results and "metadatas" in results and results["metadatas"] and results["metadatas"][0]:
            metadatas = results["metadatas"][0]
        
        if context_docs:
            raw_text = context_docs[0]
            
            cleaned_text = raw_text.replace("{", "\n• ").replace("}", "").replace("'", "").replace("[", "").replace("]", "")
            
            if len(cleaned_text) > 700:
                cleaned_text = cleaned_text[:700] + "\n\n..."

            if is_hindi:
                response_message = f"📋 **चालान विवरण (Invoice Details):**\n\n{cleaned_text}"
            else:
                response_message = f"📋 **Invoice Details:**\n\n{cleaned_text}"
        else:
            if is_hindi:
                response_message = "क्षमा करें, मुझे इस चालान या डेटा की कोई जानकारी नहीं मिली। कृपया सही चालान नंबर दर्ज करें।"
            else:
                response_message = "Sorry, I couldn't find any matching invoice in the database. Please check the invoice number and try again."
        
        return {
            "success": True,
            "response": response_message,
            "sources": metadatas
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "success": True, 
            "response": "Hello! I am your ShopBill AI Assistant. I received your message, but encountered a minor retrieval issue."
        }

@app.get("/api/backup-db")
async def backup_vector_db():
    try:
        backup_dir = "D:/shopbill_vector_db_backup"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(VECTOR_DB_PATH, backup_dir)
        return {"success": True, "message": f"Backup created successfully at {backup_dir}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)