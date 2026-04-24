from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
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

# ==========================================
# 2. SQLALCHEMY MODELS
# ==========================================
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
    
    # --- NEW STATS FIELDS ---
    year = Column(String)
    top_speed = Column(String)
    engine = Column(String)
    occupation = Column(String)
    
    quote = Column(String)
    description = Column(String) 
    actor_id = Column(Integer, ForeignKey("actors.id"))
    actor = relationship("DBActor", back_populates="characters")

Base.metadata.create_all(bind=engine)

# ==========================================
# 3. PYDANTIC SCHEMAS
# ==========================================
class ActorBase(BaseModel):
    name: str

class ActorResponse(ActorBase):
    id: int
    class Config:
        from_attributes = True

class CharacterBase(BaseModel):
    name: str
    car_model: str
    year: str          # <--- NEW
    top_speed: str     # <--- NEW
    engine: str        # <--- NEW
    occupation: str    # <--- NEW
    quote: str
    description: str
    actor_id: int

class CharacterResponse(CharacterBase):
    id: int
    actor: Optional[ActorResponse] = None
    class Config:
        from_attributes = True

# ==========================================
# 4. FASTAPI APP & ROUTES
# ==========================================
app = FastAPI(title="Cars Fanbase API")

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

        mcqueen = DBCharacter(
            name="Lightning McQueen", 
            car_model="Custom Piston Cup Racer", 
            year="2006",
            top_speed="198 mph",
            engine="750 HP Full Race V8",
            occupation="Professional Race Car",
            quote="Ka-chow!", 
            description="A hotshot rookie race car driven to succeed. He discovers that life is about the journey, not the finish line, after getting stranded in the forgotten town of Radiator Springs.",
            actor_id=owen.id
        )
        mater = DBCharacter(
            name="Tow Mater", 
            car_model="International Harvester Boom Truck", 
            year="1951",
            top_speed="Unknown (Faster backwards!)",
            engine="V8 with a 2-barrel carb",
            occupation="Tow Truck & Salvage Co. Owner",
            quote="Dad gum!", 
            description="A rusty but trusty tow truck with a heart of gold. He becomes Lightning McQueen's best friend and is always ready for a tractor-tipping adventure.",
            actor_id=larry.id
        )
        doc = DBCharacter(
            name="Doc Hudson", 
            car_model="Hudson Hornet", 
            year="1951",
            top_speed="112 mph (Stock) / Racing Tuned",
            engine="Twin H-Power Straight-6",
            occupation="Town Judge & Doctor",
            quote="I'll put it simple: if you're going hard enough left, you'll find yourself turning right.", 
            description="The quiet town judge and doctor with a secret past as the Fabulous Hudson Hornet, a three-time Piston Cup champion who teaches McQueen the true meaning of racing.",
            actor_id=paul.id
        )
        sally = DBCharacter(
            name="Sally Carrera", 
            car_model="Porsche 911 Carrera", 
            year="2002",
            top_speed="177 mph",
            engine="3.6-Liter Water-Cooled Flat-6",
            occupation="Attorney & Cozy Cone Motel Owner",
            quote="It's a great town. You should see it sometime.", 
            description="A former Los Angeles attorney who left the fast lane to find peace in Radiator Springs. She runs the Cozy Cone Motel and helps McQueen see the beauty of the town.",
            actor_id=bonnie.id
        )
        
        db.add_all([mcqueen, mater, doc, sally])
        db.commit()
    db.close()

@app.get("/characters/", response_model=List[CharacterResponse], tags=["API"])
def get_all_characters(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(DBCharacter).offset(skip).limit(limit).all()

@app.get("/actors/", response_model=List[ActorResponse], tags=["API"])
def get_actors(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(DBActor).offset(skip).limit(limit).all()

# ==========================================
# 5. SERVE THE FRONTEND
# ==========================================
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
