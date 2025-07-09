from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Union

from datetime import date

class InwardEntryBase(BaseModel):
    method: str
    in_no: str
    inward_date: datetime
    grn_no: str
    bill_no: str
    bill_date: str
    party_name: str
    material: str
    material_code: str
    unit: str
    bill_qty: float
    rate: float
    gst_percent: int
    unloading: str
    remarks: str
    part_no_make: str

class InwardEntryCreate(InwardEntryBase):
    pass

class InwardEntry(InwardEntryBase):
    sr_no: int
    recd_qty: Optional[float]
    amount: float
    gst_amount: float
    total_amount: float

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str        



class IssueEntryBase(BaseModel):
    issue_date: Optional[datetime]
    vendor_contractor: Optional[str]
    slip_no: Optional[int]
    material: str
    unit: Optional[str]
    quantity: float
    party_name: Optional[str]
    remarks: Optional[str]
  

class IssueEntryCreate(IssueEntryBase):
    pass

class IssueEntryUpdate(IssueEntryBase):
    pass

class IssueEntryOut(IssueEntryBase):
    sr_no: int
    cumulative_stock: Optional[float] = None

    class Config:
        orm_mode = True



class StockEntry(BaseModel):
    material: str
    stock_date: str
    inward_qty: float
    issue_qty: float
    cumulative_stock: float   