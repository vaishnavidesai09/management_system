from sqlalchemy import Column, Date, Integer, String, DateTime, Float, Text
from database import Base

class InwardEntry(Base):
    __tablename__ = "inward_entries"

    sr_no = Column(Integer, primary_key=True, index=True)
    method = Column(Text)
    in_no = Column(Text)
    inward_date = Column(DateTime)
    grn_no = Column(Text)
    bill_no = Column(Text)
    bill_date = Column(Text)
    party_name = Column(Text)
    material = Column(Text)
    material_code = Column(Text)
    unit = Column(Text)
    bill_qty = Column(Float)
    recd_qty = Column(Float, default=0)
    rate = Column(Float)
    amount = Column(Float)
    gst_percent = Column(Integer)
    gst_amount = Column(Float)
    total_amount = Column(Float)
    unloading = Column(Text)
    remarks = Column(Text)
    part_no_make = Column(Text)

class IssueEntry(Base):
    __tablename__ = "issue_entries"

    sr_no = Column(Integer, primary_key=True, index=True)
    issue_date = Column(Date, nullable=False)
    vendor_contractor = Column(String)
    slip_no = Column(String)
    material = Column(String, nullable=False)
    quantity = Column(Float)
    unit = Column(String)
    party_name = Column(String)
    remarks = Column(String)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)




class InwardEntries(Base):
    __tablename__ = 'inward_entries'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    material = Column(String(255), index=True, nullable=False)
    inward_date = Column(Date, nullable=False)
    bill_qty = Column(Float, nullable=False)

class IssueEntries(Base):
    __tablename__ = 'issue_entries'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    material = Column(String(255), index=True, nullable=False)
    issue_date = Column(Date, nullable=False)
    quantity = Column(Float, nullable=False)