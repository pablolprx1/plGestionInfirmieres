from fastapi import HTTPException, status
from app import database

def verif_role(current_user: dict, allowed_roles: list):
    if current_user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé pour ce rôle"
        )

async def verif_infirmiere_en_chef(user_id: int):
    """Vérifie si l'utilisateur est une infirmière en chef."""
    db = database.get_db()
    cursor = db.cursor()

    query_check = """
    SELECT infirmiere_en_chef
    FROM infirmiere
    WHERE id = %s
    """
    cursor.execute(query_check, (user_id,))
    result = cursor.fetchone()
    db.close()

    if not result or not result[0]:  # Si l'utilisateur n'est pas une infirmière en chef
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé: Il faut être infirmière en chef pour accéder à cette ressource.",
        )
