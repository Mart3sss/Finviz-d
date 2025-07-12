import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Base de SQLAlchemy
Base = declarative_base()

# Definir el modelo
class FinancialData(Base):
    __tablename__ = "financial_data"
    index = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    open = Column(Float)
    vol = Column(Float)
    p_s = Column(Float)
    p_eps = Column(Float)
    p_fcf = Column(Float)
    p_ocf = Column(Float)
    p_bv = Column(Float)
    mc_sales = Column(Float)
    mc_ebitda = Column(Float)
    mc_ebit = Column(Float)
    mc_net_income = Column(Float)
    ev_ebitda = Column(Float)
    ev_ebit = Column(Float)
    dividend_yield = Column(Float)
    fcf_yield = Column(Float)
    ticker = Column(String)

# Crear motor y base de datos SQLite
engine = create_engine("sqlite:///financial_data.db")
Base.metadata.create_all(engine)

# Crear sesión
Session = sessionmaker(bind=engine)
session = Session()

# Función para cargar datos desde CSV
def load_data_to_db(csv_file):
    # Leer CSV y asegurarse que la columna de fecha esté bien interpretada
    df = pd.read_csv(csv_file, parse_dates=["Date"])

    # Renombrar columnas para que coincidan con las del modelo
    df.columns = [col.strip().lower().replace("/", "_").replace(" ", "_") for col in df.columns]

    # Escribir en la base de datos
    df.to_sql("financial_data", engine, if_exists="replace", index=False)


load_data_to_db("tickers_50.csv")