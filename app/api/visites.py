from app.security import get_current_user
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app import models, database

router = APIRouter() # Création d'un routeur FastAPI

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

# ROLE: Infirmière en chef - Accès à toutes les visites
@router.get("/all", response_model=List[models.Visite])
async def read_all_visites(current_user: dict = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

    # Vérifie si l'utilisateur est une infirmière en chef
    cursor.execute("SELECT infirmiere_en_chef FROM infirmiere WHERE id = %s", (current_user["id"],))
    is_chef = cursor.fetchone()

    if not is_chef or not is_chef[0] or current_user["role"] != "infirmiere":
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
            cursor.execute("SELECT infirmiere_en_chef FROM infirmiere WHERE id = %s", (current_user["id"],))
            is_chef = cursor.fetchone()
            if not is_chef or not is_chef[0]:
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

# Création d'une visite
@router.post("/", response_model=models.Visite, status_code=status.HTTP_201_CREATED)
async def create_visite(visite: models.Visite, current_user: dict = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

    # Vérifier si l'utilisateur est autorisé à créer une visite
    if current_user["role"] not in ("infirmiere", "patient"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seules les infirmières et les patients peuvent créer des visites.",
        )
    
    # Initialiser l'ID en fonction du rôle de l'utilisateur
    if current_user["role"] == "infirmiere":
        visite.infirmiere_id = current_user["id"]
    elif current_user["role"] == "patient":
        visite.patient_id = current_user["id"]

    # Vérifier si les IDs infirmiere et patient sont valides
    if not visite.infirmiere_id or not visite.patient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'ID de l'infirmière ou du patient est manquant.",
        )

    cursor.execute("SELECT id FROM infirmiere WHERE id = %s", (visite.infirmiere_id,))
    infirmiere_existe = cursor.fetchone() is not None
    cursor.execute("SELECT id FROM patient WHERE id = %s", (visite.patient_id,))
    patient_existe = cursor.fetchone() is not None

    if not infirmiere_existe or not patient_existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "ID infirmière ou patient invalide.",
            },
        )

    # Insérer la visite dans la base de données
    query = """
    INSERT INTO visite (date_prevue, infirmiere, patient, compte_rendu_infirmiere, compte_rendu_patient)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (
        visite.date_prevue,
        visite.infirmiere_id,
        visite.patient_id,
        visite.compte_rendu_infirmiere,
        visite.compte_rendu_patient,
    )
    cursor.execute(query, values)
    db.commit()

    # Récupérer l'ID de la nouvelle visite
    visite_id = cursor.lastrowid

    # Récupérer la visite créée pour la renvoyer
    query = """
    SELECT id, date_prevue, infirmiere, patient, compte_rendu_infirmiere, compte_rendu_patient
    FROM visite
    WHERE id = %s
    """
    cursor.execute(query, (visite_id,))
    new_visite = cursor.fetchone()
    db.close()

    if not new_visite:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de la visite nouvellement créée.",
        )

    return models.Visite(
        id=new_visite[0],
        date_prevue=new_visite[1],
        infirmiere_id=new_visite[2],
        patient_id=new_visite[3],
        compte_rendu_infirmiere=new_visite[4],
        compte_rendu_patient=new_visite[5],
    )

# UPDATE
@router.put("/{visite_id}", response_model=models.Visite)
async def update_visite(
    visite_id: int, visite_update: models.Visite, current_user: dict = Depends(get_current_user)
):
    db = database.get_db()
    cursor = db.cursor()

    # Récupérer la visite actuelle
    query_get_visite = """
    SELECT infirmiere, patient
    FROM visite
    WHERE id = %s
    """
    cursor.execute(query_get_visite, (visite_id,))
    visite_info = cursor.fetchone()

    if not visite_info:
        raise HTTPException(status_code=404, detail="Visite non trouvée")

    infirmiere_id, patient_id = visite_info

    # Vérifier les autorisations
    if current_user["role"] == "infirmiere":
        if infirmiere_id != current_user["id"]:
            cursor.execute("SELECT infirmiere_en_chef FROM infirmiere WHERE id = %s", (current_user["id"],))
            is_chef = cursor.fetchone()
            if not is_chef or not is_chef[0]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'êtes pas autorisé à modifier cette visite.",
                )
    elif current_user["role"] == "patient":
        if patient_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à modifier cette visite.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle inconnu."
        )

    # Mettre à jour la visite
    query_update = """
    UPDATE visite
    SET date_prevue = %s, compte_rendu_infirmiere = %s, compte_rendu_patient = %s
    WHERE id = %s
    """
    values = (
        visite_update.date_prevue,
        visite_update.compte_rendu_infirmiere,
        visite_update.compte_rendu_patient,
        visite_id,
    )
    cursor.execute(query_update, values)
    db.commit()

    # Récupérer la visite mise à jour
    query_get_updated_visite = """
    SELECT id, date_prevue, infirmiere, patient, compte_rendu_infirmiere, compte_rendu_patient
    FROM visite
    WHERE id = %s
    """
    cursor.execute(query_get_updated_visite, (visite_id,))
    updated_visite = cursor.fetchone()
    db.close()

    if not updated_visite:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de la visite mise à jour.",
        )

    return models.Visite(
        id=updated_visite[0],
        date_prevue=updated_visite[1],
        infirmiere_id=updated_visite[2],
        patient_id=updated_visite[3],
        compte_rendu_infirmiere=updated_visite[4],
        compte_rendu_patient=updated_visite[5],
    )

# DELETE
@router.delete("/{visite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visite(visite_id: int, current_user: dict = Depends(get_current_user)):
    db = database.get_db()
    cursor = db.cursor()

    # Récupérer la visite actuelle
    query_get_visite = """
    SELECT infirmiere, patient
    FROM visite
    WHERE id = %s
    """
    cursor.execute(query_get_visite, (visite_id,))
    visite_info = cursor.fetchone()

    if not visite_info:
        raise HTTPException(status_code=404, detail="Visite non trouvée")

    infirmiere_id, patient_id = visite_info

    # Vérifier les autorisations
    if current_user["role"] == "infirmiere":
        if infirmiere_id != current_user["id"]:
            cursor.execute("SELECT infirmiere_en_chef FROM infirmiere WHERE id = %s", (current_user["id"],))
            is_chef = cursor.fetchone()
            if not is_chef or not is_chef[0]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'êtes pas autorisé à supprimer cette visite.",
                )
    elif current_user["role"] == "patient":
        if patient_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à supprimer cette visite.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle inconnu."
        )

    # Supprimer la visite
    query_delete = """
    DELETE FROM visite
    WHERE id = %s
    """
    cursor.execute(query_delete, (visite_id,))
    db.commit()
    db.close()

    return
