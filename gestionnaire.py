import json
import os
from etudiant import Etudiant

DOSSIER = os.path.dirname(os.path.abspath(__file__))


def cle_nom(etudiant):
    return etudiant.nom.lower()


def cle_note(etudiant):
    return etudiant.note


class GestionnaireEtudiants:
    def __init__(self, fichier="etudiants.json"):
        self.fichier = os.path.join(DOSSIER, fichier)
        self.etudiants = []

    # ----- Fichier JSON -----
    def sauvegarder(self):
        donnees = []
        for etudiant in self.etudiants:
            donnees.append(etudiant.en_dictionnaire())
        with open(self.fichier, "w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier, indent=4, ensure_ascii=False)

    def charger(self):
        try:
            with open(self.fichier, "r", encoding="utf-8") as fichier:
                donnees = json.load(fichier)
        except FileNotFoundError:
            donnees = []

        self.etudiants = []
        for d in donnees:
            self.etudiants.append(Etudiant.depuis_dictionnaire(d))

    # ----- Gestion de la liste -----
    def ajouter(self, etudiant):
        self.etudiants.append(etudiant)
        self.sauvegarder()

    def supprimer(self, etudiant):
        self.etudiants.remove(etudiant)
        self.sauvegarder()

    def modifier(self, etudiant, nom, age, note):
        etudiant.nom = nom
        etudiant.age = age
        etudiant.note = note
        self.sauvegarder()

    def nom_existe(self, nom, ignorer=None):
        """True si un autre étudiant porte déjà ce nom."""
        for etudiant in self.etudiants:
            if etudiant is not ignorer and etudiant.nom.lower() == nom.lower():
                return True
        return False

    # ----- Recherche, tri, filtre -----
    def obtenir(self, tri="A-Z", filtre="Tous", recherche=""):
        recherche = recherche.strip().lower()
        resultat = []
        for etudiant in self.etudiants:
            if filtre == "Admis" and not etudiant.est_admis():
                continue
            if filtre == "Ajournés" and etudiant.est_admis():
                continue
            if recherche not in etudiant.nom.lower():
                continue
            resultat.append(etudiant)

        if tri == "A-Z":
            resultat.sort(key=cle_nom)
        else:
            resultat.sort(key=cle_note, reverse=True)
        return resultat

    # ----- Statistiques -----
    def statistiques(self):
        """Retourne un dictionnaire de statistiques, ou None si la liste est vide."""
        nombre = len(self.etudiants)
        if nombre == 0:
            return None

        somme = 0
        admis = 0
        repartition = [0, 0, 0, 0]
        for etudiant in self.etudiants:
            somme = somme + etudiant.note
            if etudiant.est_admis():
                admis = admis + 1
            if etudiant.note < 5:
                repartition[0] = repartition[0] + 1
            elif etudiant.note < 10:
                repartition[1] = repartition[1] + 1
            elif etudiant.note < 15:
                repartition[2] = repartition[2] + 1
            else:
                repartition[3] = repartition[3] + 1

        return {
            "nombre": nombre,
            "moyenne": somme / nombre,
            "admis": admis,
            "ajournes": nombre - admis,
            "taux": admis / nombre,
            "meilleurs": sorted(self.etudiants, key=cle_note, reverse=True)[:3],
            "repartition": repartition,
        }