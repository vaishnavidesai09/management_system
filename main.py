from fastapi import FastAPI, Depends,  HTTPException, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, crud, schemas
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone

from fastapi import Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import status

from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io

import pandas as pd 
import datetime
from models import InwardEntry
from database import SessionLocal
import crud, schemas
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from fastapi.staticfiles import StaticFiles



load_dotenv()  # Load environment variables from .env

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
app.mount("/img", StaticFiles(directory="img"), name="img")
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/entries/", response_model=schemas.InwardEntry)
def create(entry: schemas.InwardEntryCreate, db: Session = Depends(get_db)):
    return crud.create_entry(db, entry)

@app.get("/entries/", response_model=list[schemas.InwardEntry])
def read_entries(skip: int = 0, limit: int = 50000, db: Session = Depends(get_db)):
    return crud.get_entries(db, skip=skip, limit=limit)

@app.get("/entries/{sr_no}", response_model=schemas.InwardEntry)
def read_entry(sr_no: int, db: Session = Depends(get_db)):
    db_entry = crud.get_entry(db, sr_no)
    if db_entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return db_entry

@app.get("/entries/filter", response_model=list[schemas.InwardEntry])
def filter_entries(
    date_filter: Optional[date] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    return crud.get_filtered_entries(db, date_filter=date_filter, month=month, year=year)

@app.put("/entries/{sr_no}", response_model=schemas.InwardEntry)
def update_entry(sr_no: int, entry: schemas.InwardEntryCreate, db: Session = Depends(get_db)):
    updated = crud.update_entry(db, sr_no, entry)
    if updated is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return updated

@app.delete("/entries/{sr_no}")
def delete_entry(sr_no: int, db: Session = Depends(get_db)):
    success = crud.delete_entry(db, sr_no)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": f"Entry {sr_no} deleted and sr_no reordered."}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/download/")
def download_excel(
    from_date: datetime.date = Query(None),
    to_date: datetime.date = Query(None),
    party_name: str = Query(None),
    material: str = Query(None),
    in_no: str = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(InwardEntry)

    if from_date:
        query = query.filter(InwardEntry.inward_date >= from_date)
    if to_date:
        query = query.filter(InwardEntry.inward_date <= to_date)
    if party_name:
        query = query.filter(InwardEntry.party_name.ilike(f"%{party_name}%"))
    if material:
        query = query.filter(InwardEntry.material.ilike(f"%{material}%"))
    if in_no:
        query = query.filter(InwardEntry.in_no.ilike(f"%{in_no}%"))

    entries = query.all()

    data = [
        {
            "sr_no": e.sr_no,
            "method": e.method,
            "in_no": e.in_no,
            "inward_date": e.inward_date,
            "grn_no": e.grn_no,
            "bill_no": e.bill_no,
            "bill_date": e.bill_date,
            "party_name": e.party_name,
            "material": e.material,
            "material_code": e.material_code,
            "unit": e.unit,
            "bill_qty": e.bill_qty,
            "rate": e.rate,
            'amount':e.amount,
            "gst_percent": e.gst_percent,
            'gst_amount': e.gst_amount,
            "total_amount":e.total_amount,
            "unloading": e.unloading,
            "remarks": e.remarks,
            "part_no_make": e.part_no_make,
        }
        for e in entries
    ]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inward Entries")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inward_entries.xlsx"},
    )






@app.post("/issue_entries/", response_model=schemas.IssueEntryOut)
def create_issue_entry(entry: schemas.IssueEntryCreate, db: Session = Depends(get_db)):
    return crud.create_issue_entry(db, entry)

@app.get("/issue_entries/", response_model=List[schemas.IssueEntryOut])
def read_all_issue_entries(db: Session = Depends(get_db)):
    return crud.get_all_issue_entries(db)

@app.get("/issue_entries/{sr_no}", response_model=schemas.IssueEntryOut)
def read_issue_entry(sr_no: int, db: Session = Depends(get_db)):
    db_entry = crud.get_issue_entry(db, sr_no)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db_entry.cumulative_stock = crud.calculate_cumulative_stock(db, db_entry.material, db_entry.issue_date)
    return db_entry

@app.put("/issue_entries/{sr_no}", response_model=schemas.IssueEntryOut)
def update_issue_entry(sr_no: int, entry: schemas.IssueEntryUpdate, db: Session = Depends(get_db)):
    return crud.update_issue_entry(db, sr_no, entry)

@app.delete("/issue_entries/{sr_no}")
def delete_issue_entry(sr_no: int, db: Session = Depends(get_db)):
    crud.delete_issue_entry(db, sr_no)
    return {"detail": "Deleted"}




    

@app.get("/stock", response_class=HTMLResponse)
def stock_page():
    with open("stock.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/stock-data", response_model=list[schemas.StockEntry])
def stock_data(db: Session = Depends(get_db)):
    rows = crud.get_stock_data(db)
    result = [
        {
            "material": r[0],
            "stock_date": str(r[1]),
            "inward_qty": r[2],
            "issue_qty": r[3],
            "cumulative_stock": r[4]
        } for r in rows
    ]
    return JSONResponse(content=result)



from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home_page():
    with open("home.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/inward", response_class=HTMLResponse)
def inward_page():
    with open("inward.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/issue", response_class=HTMLResponse)
def issue_page():
    with open("issue.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/stock", response_class=HTMLResponse)
def stock_page():
    with open("stock.html", "r", encoding="utf-8") as f:
        return f.read()
    

templates = Jinja2Templates(directory="templates")    
@app.get("/home", response_class=HTMLResponse)
def stock_page():
    with open("home.html", "r", encoding="utf-8") as f:
        return f.read()