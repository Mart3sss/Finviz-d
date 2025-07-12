from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as SessionType
from database import Session, FinancialData  # Asumiendo que database.py está en el mismo directorio
from math import isnan, isinf
app = FastAPI()

# Middleware CORS para permitir acceso desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para obtener una sesión de la base de datos
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/data")
def get_data(db: SessionType = Depends(get_db)):
    data = db.query(FinancialData).all()
    response = []
    for d in data:
        try:
            item = {
                "index": d.index,
                "date": d.date,
                "ticker": d.ticker,
                "close": d.close,
                "high": d.high,
                "low": d.low,
                "open": d.open,
                "vol": d.vol,
                "p_s": d.p_s,
                "p_eps": d.p_eps,
                "p_fcf": d.p_fcf,
                "p_ocf": d.p_ocf,
                "p_bv": d.p_bv,
                "mc_sales": d.mc_sales,
                "mc_ebitda": d.mc_ebitda,
                "mc_ebit": d.mc_ebit,
                "mc_net_income": d.mc_net_income,
                "ev_ebitda": d.ev_ebitda,
                "ev_ebit": d.ev_ebit,
                "dividend_yield": d.dividend_yield,
                "fcf_yield": d.fcf_yield,
            }

            # Validar valores float para que no haya valores NaN o infinitos
            for k, v in item.items():
                if isinstance(v, float):
                    if isnan(v) or isinf(v):
                        item[k] = None  # Cambiar valores inválidos a None

            response.append(item)
        except Exception as e:
            print(f"Error con registro index {d.index}: {e}")
    return response