import pandas as pd
from sqlalchemy import create_engine
import urllib.parse

# Load Excel file
df = pd.read_excel('cleaned_data_issue.xlsx', sheet_name='Issue_material')

# Proper username and password
user = urllib.parse.quote_plus('vaishnavi')
password = urllib.parse.quote_plus('Vaishu@2003')  # make sure this is correct

# Database and host details
host = '127.0.0.1'
database = 'inward_db'
password= 'Vaishu%402003'
port = '3306'
user = 'root'

# Create SQLAlchemy engine
engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

# Upload to MySQL
df.to_sql(name='issue_entries', con=engine, if_exists='replace', index=False)
