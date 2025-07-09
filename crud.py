from sqlalchemy.orm import Session
from sqlalchemy import func
from models import InwardEntry
import models
from schemas import InwardEntryCreate
from fastapi import HTTPException
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from models import User
from sqlalchemy import text
#from auth import get_password_hash # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy.sql import extract, and_
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, union_all, literal_column, null

import schemas




# Utility function for calculations
def calculate_amounts(entry: InwardEntryCreate):
    amount = entry.rate * entry.bill_qty
    gst_amount = amount * entry.gst_percent / 100
    total_amount = amount + gst_amount
    recd_qty = entry.bill_qty
    return amount, gst_amount, total_amount, recd_qty

# Create new entry with manually incremented sr_no
def create_entry(db: Session, entry: InwardEntryCreate):
    # Get the next sr_no manually
    max_sr_no = db.query(func.max(InwardEntry.sr_no)).scalar()
    next_sr_no = (max_sr_no or 0) + 1

    amount, gst_amount, total_amount,recd_qty = calculate_amounts(entry)

    db_entry = InwardEntry(
        sr_no=next_sr_no,
        **entry.model_dump(),
        amount=amount,
        recd_qty=recd_qty,
        gst_amount=gst_amount,
        total_amount=total_amount
        
    )

    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    reorder_sr_no(db)  # ensure sr_no remains in sequence

    return db_entry

# Get all entries with optional pagination
def get_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(InwardEntry).order_by(InwardEntry.sr_no).offset(skip).limit(limit).all()

# Get one entry by sr_no
def get_entry(db: Session, sr_no: int):
    return db.query(InwardEntry).filter(InwardEntry.sr_no == sr_no).first()

# Delete entry and reorder sr_no
def delete_entry(db: Session, sr_no: int):
    entry = get_entry(db, sr_no)
    if entry:
        db.delete(entry)
        db.commit()
        reorder_sr_no(db)
        return True
    raise HTTPException(status_code=404, detail="Entry not found")

# Update entry and recalculate amounts
def update_entry(db: Session, sr_no: int, new_data: InwardEntryCreate):
    entry = get_entry(db, sr_no)
    if entry:
        amount, gst_amount, total_amount,recd_qty = calculate_amounts(new_data)
        for field, value in new_data.model_dump().items():
            setattr(entry, field, value)
        entry.amount = amount
        entry.gst_amount = gst_amount
        entry.total_amount = total_amount
        recd_qty=recd_qty
        db.commit()
        db.refresh(entry)
        reorder_sr_no(db)
        return entry
    raise HTTPException(status_code=404, detail="Entry not found")

# Renumber sr_no in sequential order starting from 1
def reorder_sr_no(db: Session):
    entries = db.query(InwardEntry).order_by(InwardEntry.sr_no).all()
    for idx, entry in enumerate(entries, start=1):
        entry.sr_no = idx
    db.commit()




def get_filtered_entries(
    db: Session,
    date_filter: Optional[date] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
):
    query = db.query(InwardEntry)

    if date_filter:
        query = query.filter(InwardEntry.inward_date == date_filter)

    elif month and year:
        query = query.filter(
            and_(
                extract('month', InwardEntry.inward_date) == month,
                extract('year', InwardEntry.inward_date) == year
            )
        )

    elif year:
        query = query.filter(extract('year', InwardEntry.inward_date) == year)

    return query.order_by(InwardEntry.sr_no).all()







def create_issue_entry(db: Session, entry: schemas.IssueEntryCreate):
    # 1. Get the max sr_no from existing entries
    max_sr = db.query(func.max(models.IssueEntry.sr_no)).scalar()
    next_sr = 1 if max_sr is None else max_sr + 1

    # 2. Convert entry to dictionary, insert sr_no
    entry_data = entry.model_dump()
    entry_data["sr_no"] = next_sr

    # 3. Add and commit
    db_entry = models.IssueEntry(**entry_data)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return db_entry


def get_issue_entry(db: Session, sr_no: int):
    return db.query(models.IssueEntry).filter(models.IssueEntry.sr_no == sr_no).first()


def get_all_issue_entries(db: Session):
    entries = db.query(models.IssueEntry).all()
    result = []

    for entry in entries:
        if entry is None:
            print("[Warning] Skipping None entry in issue_entries")
            continue

        if not entry.material or not entry.issue_date:
            print(f"[Warning] Skipping entry with missing material or issue_date: {entry}")
            entry.cumulative_stock = None
        else:
            try:
                entry.cumulative_stock = calculate_cumulative_stock(db, entry.material, entry.issue_date)
            except Exception as e:
                print(f"[Error] Failed to calculate cumulative stock for entry {entry.sr_no}: {e}")
                entry.cumulative_stock = None

        result.append(entry)

    return result


def update_issue_entry(db: Session, sr_no: int, updated: schemas.IssueEntryUpdate):
    db_entry = get_issue_entry(db, sr_no)
    if db_entry:
        for k, v in updated.model_dump(exclude_unset=True).items():
            setattr(db_entry, k, v)
        db.commit()
        try:
            db.refresh(db_entry)
        except Exception as e:
            print(f"[Error] Could not refresh updated entry: {e}")
    else:
        print(f"[Warning] No entry found to update with sr_no={sr_no}")
    return db_entry


def delete_issue_entry(db: Session, sr_no: int):
    db_entry = get_issue_entry(db, sr_no)
    if db_entry:
        db.delete(db_entry)
        db.commit()
    else:
        print(f"[Warning] No entry found to delete with sr_no={sr_no}")
    return db_entry


def calculate_cumulative_stock(db: Session, material: str, as_of_date: date) -> float:
    try:
        inward_sum = db.execute(
            text("""
                SELECT IFNULL(SUM(bill_qty), 0)
                FROM inward_entries
                WHERE material = :material AND DATE(inward_date) <= :as_of_date
            """),
            {"material": material, "as_of_date": as_of_date}
        ).scalar()

        issue_sum = db.execute(
            text("""
                SELECT IFNULL(SUM(quantity), 0)
                FROM issue_entries
                WHERE material = :material AND DATE(issue_date) <= :as_of_date
            """),
            {"material": material, "as_of_date": as_of_date}
        ).scalar()

        return float(inward_sum or 0) - float(issue_sum or 0)

    except Exception as e:
        print(f"[Error] Failed to calculate cumulative stock for {material} as of {as_of_date}: {e}")
        return 0.0
    



def get_stock_data(db: Session):
    query = """
    WITH combined_data AS (
        SELECT
            material,
            inward_date AS stock_datetime,
            bill_qty AS inward_qty,
            0 AS issue_qty
        FROM inward_entries

        UNION ALL

        SELECT
            material,
            issue_date AS stock_datetime,
            0 AS inward_qty,
            quantity AS issue_qty
        FROM issue_entries
    ),
    numbered_data AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY material ORDER BY stock_datetime) AS row_num
        FROM combined_data
    )
    SELECT
        material,
        DATE(stock_datetime) AS stock_date,
        inward_qty,
        issue_qty,
        SUM(inward_qty) OVER (PARTITION BY material ORDER BY row_num) -
        SUM(issue_qty) OVER (PARTITION BY material ORDER BY row_num) AS cumulative_stock
    FROM numbered_data
    ORDER BY material, stock_date, row_num;
    """
    rows = db.execute(text(query)).fetchall()
    return rows

