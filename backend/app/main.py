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

# Pass the get_db function as the dependency
def database_health_check(db: Session = Depends(get_db)): # The Depends function represents the function as the dependency for FastAPI to manage its lifecycle.

    # The execute method (of the session) executes an SQL Query.
    # The text function represents the string as a proper SQL query instead of a mere string.
    result = db.execute(text('SELECT version()'))

    return {'database': result.scalar()} # the scalar method returns the first column of the first row.
