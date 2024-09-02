from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Boolean, select
import random
from typing import List
from pydantic import BaseModel

app = FastAPI()

# Connect to Database
DATABASE_URL = 'sqlite:///./cafes.db'  # URI=connection detail
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Cafe TABLE Configuration
class Cafe(Base):
    __tablename__ = "cafes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(250), unique=True, nullable=False)
    map_url = Column(String(500), nullable=False)
    img_url = Column(String(500), nullable=False)
    location = Column(String(250), nullable=False)
    seats = Column(String(250), nullable=False)
    has_toilet = Column(Boolean, nullable=False)
    has_wifi = Column(Boolean, nullable=False)
    has_sockets = Column(Boolean, nullable=False)
    can_take_calls = Column(Boolean, nullable=False)
    coffee_price = Column(String(250), nullable=True)

Base.metadata.create_all(bind=engine)

# Pydantic models
class CafeBase(BaseModel):
    name: str
    map_url: str
    img_url: str
    location: str
    seats: str
    has_toilet: bool
    has_wifi: bool
    has_sockets: bool
    can_take_calls: bool
    coffee_price: str

class CafeCreate(CafeBase):
    pass

class CafeResponse(CafeBase):
    id: int

    class Config:
        from_attributes = True  # Updated from `orm_mode`

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_model=List[CafeResponse])
def read_cafes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    cafes = db.execute(select(Cafe).offset(skip).limit(limit)).scalars().all()
    return cafes

@app.get("/random", response_model=CafeResponse)
def random_cafe(db: Session = Depends(get_db)):
    cafes = db.execute(select(Cafe)).scalars().all()
    if not cafes:
        raise HTTPException(status_code=404, detail="No cafes available")
    random_cafe = random.choice(cafes)
    return random_cafe

@app.get("/all", response_model=List[CafeResponse])
def all_cafe(db: Session = Depends(get_db)):
    cafes = db.execute(select(Cafe)).scalars().all()
    return cafes

@app.get("/search", response_model=List[CafeResponse])
def find_cafe(loc: str = Query(..., alias="loc"), db: Session = Depends(get_db)):
    cafes = db.execute(select(Cafe).where(Cafe.location == loc.strip('\'"'))).scalars().all()
    if not cafes:
        raise HTTPException(status_code=404, detail="Sorry, we don't have a cafe at the location")
    return cafes

@app.post("/add", response_model=CafeResponse)
def add_cafe(cafe: CafeCreate, db: Session = Depends(get_db)):
    new_cafe = Cafe(**cafe.dict())
    db.add(new_cafe)
    db.commit()
    db.refresh(new_cafe)
    return new_cafe

@app.patch("/update-price/{cafe_id}", response_model=CafeResponse)
def update_price(cafe_id: int, new_price: str = Query(...), db: Session = Depends(get_db)):
    cafe = db.query(Cafe).filter(Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    cafe.coffee_price = new_price
    db.commit()
    db.refresh(cafe)
    return cafe

@app.delete("/report-closed/{cafe_id}", response_model=dict)
def delete_cafe(cafe_id: int, api_key: str = Query(...), db: Session = Depends(get_db)):
    if api_key != "TopSecretAPIKey":
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")
    cafe = db.query(Cafe).filter(Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    db.delete(cafe)
    db.commit()
    return {"success": "Successfully deleted the cafe from the database."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
