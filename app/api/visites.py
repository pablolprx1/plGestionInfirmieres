
from app.security import get_current_user
from app.utils import verif_infirmiere_en_chef
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app import models, database

router = APIRouter()

@router.get("/")
async def read_visites(current_user: int = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

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
    JOIN
        infirmiere i ON v.infirmiere = i.id
    JOIN
        personne_login pl ON i.id = pl.id
    WHERE
        pl.id = %s
    """
    cursor.execute(query, (current_user,))
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

@router.get("/all")
async def read_all_visites(current_user: int = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

    # Vérifie si l'utilisateur est une infirmière en chef
    verif_infirmiere_en_chef(current_user)

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

# Route pour récupérer une visite spécifique
@router.get("/{visite_id}")
async def read_visite(visite_id: int, current_user: int = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

    # Vérifie si l'utilisateur est une infirmière en chef
    try:
        await verif_infirmiere_en_chef(current_user)
        is_chef = True
    except HTTPException:
        is_chef = False

    # Vérifie si l'utilisateur est l'infirmière concernée par la visite
    query_check_infirmiere = """
    SELECT infirmiere
    FROM visite
    WHERE id = %s
    """
    cursor.execute(query_check_infirmiere, (visite_id,))
    result_infirmiere = cursor.fetchone()

    if not result_infirmiere:  # Si la visite n'existe pas
        db.close()
        raise HTTPException(status_code=404, detail="Visite non trouvée")

    is_infirmiere_concernee = result_infirmiere[0] == current_user

    # Si l'utilisateur n'est ni infirmière en chef ni l'infirmière concernée, accès refusé
    if not is_chef and not is_infirmiere_concernee:
        db.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé: Vous devez être infirmière en chef ou l'infirmière concernée par cette visite.",
        )

    # Requête pour récupérer les détails de la visite
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

    # Convertit les résultats en objet Visite
    visite = models.Visite(
        id=visite_data[0],
        date_prevue=visite_data[1],
        infirmiere_id=visite_data[2],
        patient_id=visite_data[3],
        compte_rendu_infirmiere=visite_data[4],
        compte_rendu_patient=visite_data[5],
    )

    return visite