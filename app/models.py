from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class Infirmiere(BaseModel):
    id: int
    fichier_photo: Optional[str] = None

class Personne(BaseModel):
    id: int
    nom: str
    prenom: str
    sexe: str
    date_naiss: Optional[date] = None
    date_deces: Optional[date] = None
    ad1: Optional[str] = None
    ad2: Optional[str] = None
    cp: Optional[int] = None
    ville: Optional[str] = None
    tel_fixe: Optional[str] = None
    tel_port: Optional[str] = None
    mail: Optional[str] = None

class PersonneLogin(BaseModel):
    id: int
    login: str
    mp: str
    derniere_connexion: Optional[date] = None
    nb_tentative_erreur: int = 0

# Modèle pour les visites (exemple)
class Visite(BaseModel):
    id: Optional[int] = None
    date_prevue: Optional[datetime] = None
    infirmiere_id: Optional[int] = None
    patient_id: Optional[int] = None
    compte_rendu_infirmiere: Optional[str] = None
    compte_rendu_patient: Optional[str] = None
