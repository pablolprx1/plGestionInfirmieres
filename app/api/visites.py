from app.security import get_current_user
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app import models, database

router = APIRouter()

# Accès à toutes les visites d'un utilisateur (infirmière ou patient)
@router.get("/", response_model=List[models.Visite])
async def read_visites(current_user: dict = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

    # Détermine le rôle de l'utilisateur et adapter la requête
    if current_user["role"] == "infirmiere":
        query = """
        SELECT
            v.id,
            v.date_prevue,
            v.patient AS patient_id,
            v.compte_rendu_infirmiere,
            v.compte_rendu_patient
        FROM
            visite v
        WHERE
            v.infirmiere = %s
        """
    else:  # Rôle est "patient"
        query = """
        SELECT
            v.id,
            v.date_prevue,
            v.infirmiere AS infirmiere_id,
            v.compte_rendu_infirmiere,
            v.compte_rendu_patient
        FROM
            visite v
        WHERE
            v.patient = %s
        """
    cursor.execute(query, (current_user["id"],))
    visites_data = cursor.fetchall()
    db.close()

    visites = [
        models.Visite(
            id=visite[0],
            date_prevue=visite[1],
            patient_id=visite[2] if current_user["role"] == "infirmiere" else None,
            infirmiere_id=visite[2] if current_user["role"] == "patient" else None,
            compte_rendu_infirmiere=visite[3],
            compte_rendu_patient=visite[4],
        )
        for visite in visites_data
    ]

    return visites

# Accès à une visite spécifique
@router.get("/{visite_id}", response_model=models.Visite)
async def read_visite(visite_id: int, current_user: dict = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

    # Récupérer les infos de la visite
    query_visite = """
    SELECT infirmiere, patient
    FROM visite
    WHERE id = %s
    """
    cursor.execute(query_visite, (visite_id,))
    visite_info = cursor.fetchone()

    if not visite_info:
        raise HTTPException(status_code=404, detail="Visite non trouvée")

    infirmiere_id, patient_id = visite_info

    # Vérifier les droits
    if current_user["role"] == "infirmiere":
        if infirmiere_id != current_user["id"]:
            cursor.execute("SELECT id FROM administrateur WHERE id = %s", (current_user["id"],))
            is_chef = cursor.fetchone() is not None
            if not is_chef:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accès refusé : Vous n'êtes pas l'infirmière concernée par cette visite ni une infirmière en chef.",
                )
    elif current_user["role"] == "patient":
        if patient_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé : Ce n'est pas votre visite.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle inconnu."
        )

    query = """
    SELECT
        v.id,
        v.date_prevue,
        v.infirmiere AS infirmiere_id,
        v.patient AS patient_id,
        v.compte_rendu_infirmiere,
        v.compte_rendu_patient
    FROM
        visite v
    WHERE
        v.id = %s
    """
    cursor.execute(query, (visite_id,))
    visite_data = cursor.fetchone()
    db.close()

    if not visite_data:
        raise HTTPException(status_code=404, detail="Visite non trouvée")

    visite = models.Visite(
        id=visite_data[0],
        date_prevue=visite_data[1],
        infirmiere_id=visite_data[2],
        patient_id=visite_data[3],
        compte_rendu_infirmiere=visite_data[4],
        compte_rendu_patient=visite_data[5],
    )

    return visite

# ROLE: Infirmière en chef - Accès à toutes les visites
@router.get("/all", response_model=List[models.Visite])
async def read_all_visites(current_user: dict = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

    # Vérifie si l'utilisateur est une infirmière en chef
    cursor.execute("SELECT id FROM administrateur WHERE id = %s", (current_user["id"],))
    is_chef = cursor.fetchone() is not None

    if not is_chef or current_user["role"] != "infirmiere":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé : Vous devez être une infirmière en chef pour accéder à toutes les visites.",
        )

    query = """
    SELECT
        v.id,
        v.date_prevue,
        v.infirmiere AS infirmiere_id,
        v.patient AS patient_id,
        v.compte_rendu_infirmiere,
        v.compte_rendu_patient
    FROM
        visite v
    """
    cursor.execute(query)
    visites_data = cursor.fetchall()
    db.close()

    visites = [
        models.Visite(
            id=visite[0],
            date_prevue=visite[1],
            infirmiere_id=visite[2],
            patient_id=visite[3],
            compte_rendu_infirmiere=visite[4],
            compte_rendu_patient=visite[5],
        )
        for visite in visites_data
    ]

    return visites
