from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app import models, database, security

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = database.get_db()
    cursor = db.cursor()
    
    # Vérifie si c'est une infirmière ou un patient
    query = """
    SELECT 
        pl.id, 
        pl.mp,
        IF(i.id IS NOT NULL, 'infirmiere', 'patient') AS role
    FROM personne_login pl
    LEFT JOIN infirmiere i ON pl.id = i.id
    LEFT JOIN patient p ON pl.id = p.id
    WHERE pl.login = %s
    """
    cursor.execute(query, (form_data.username,))
    user = cursor.fetchone()
    db.close()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id, hashed_password, role = user
    if not security.verify_password(form_data.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user_id), "role": role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
