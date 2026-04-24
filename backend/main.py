from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List, Optional

# ==========================================
# 1. DATABASE SETUP
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./cars_fanbase.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBActor(Base):
    __tablename__ = "actors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    characters = relationship("DBCharacter", back_populates="actor")

class DBCharacter(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    car_model = Column(String)
    quote = Column(String)
    actor_id = Column(Integer, ForeignKey("actors.id"))
    actor = relationship("DBActor", back_populates="characters")

Base.metadata.create_all(bind=engine)

# ==========================================
# 2. SCHEMAS
# ==========================================
class ActorBase(BaseModel): name: str
class ActorResponse(ActorBase):
    id: int
    class Config: from_attributes = True

class CharacterBase(BaseModel):
    name: str
    car_model: str
    quote: str
    actor_id: int

class CharacterResponse(CharacterBase):
    id: int
    actor: Optional[ActorResponse] = None
    class Config: from_attributes = True

# ==========================================
# 3. APP SETUP & CORS
# ==========================================
app = FastAPI(title="Cars Fanbase API")

# Allow the frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend's actual URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    if db.query(DBActor).first() is None:
        owen = DBActor(name="Owen Wilson")
        larry = DBActor(name="Larry the Cable Guy")
        paul = DBActor(name="Paul Newman")
        bonnie = DBActor(name="Bonnie Hunt")
        db.add_all([owen, larry, paul, bonnie])
        db.commit()

        mcqueen = DBCharacter(name="Lightning McQueen", car_model="Custom 2006 Piston Cup Racer", quote="Ka-chow!", actor_id=owen.id)
        mater = DBCharacter(name="Tow Mater", car_model="1951 International Harvester Boom Truck", quote="Dad gum!", actor_id=larry.id)
        doc = DBCharacter(name="Doc Hudson", car_model="1951 Hudson Hornet", quote="I'll put it simple: if you're going hard enough left...", actor_id=paul.id)
        sally = DBCharacter(name="Sally Carrera", car_model="2002 Porsche 911 Carrera", quote="It's a great town...", actor_id=bonnie.id)
        db.add_all([mcqueen, mater, doc, sally])
        db.commit()
    db.close()

# ==========================================
# 4. API ENDPOINTS
# ==========================================
@app.get("/characters/", response_model=List[CharacterResponse])
def get_all_characters(db: Session = Depends(get_db)):
    return db.query(DBCharacter).all()

@app.get("/actors/", response_model=List[ActorResponse])
def get_actors(db: Session = Depends(get_db)):
    return db.query(DBActor).all()