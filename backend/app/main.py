from fastapi import FastAPI, Depends

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

@app.get('/health')
def health_check():
    return {'status': 'ok'}

@app.get('/db-health')
def database_health_check(db: Session = Depends(get_db)):
    result = db.execute(text('SELECT version()'))

    return {'database': result.scalar()}
