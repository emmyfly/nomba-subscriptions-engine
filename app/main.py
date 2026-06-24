from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base
from app.models.plan import Plan
from app.models.subscriber import Subscriber
from app.models.payment import Paymen

app = FastAPI(
     title="Nomba subscription Engine",
     description="Managed subscrition on Nomba payment infratsructure",
     version="0.1.0",

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return{
        "name":"Nomba Subscrition Engine",
        "status":"running",
        "docs": "Go to /docs to see all endpoints",
    }