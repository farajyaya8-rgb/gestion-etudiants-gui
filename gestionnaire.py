import json
import os
import sqlite3
from etudiant import Etudiant

DOSSIER = os.path.dirname(os.path.abspath(__file__))


def cle_nom(etudiant):
    return etudiant.nom.lower()


def cle_note(etudiant):
    return etudiant.note


class GestionnaireEtudiants:
    def __init__(self, fichier_db="etudiants.db"):
        self.fichier_json = os.path.join(DOSSIER, "etudiants.json")
        self.connexion = sqlite3.connect(os.path.join(DOSSIER, fichier_db))
        self.etudiants = []
        self.creer_table()
        self.migrer_json()

    # ----- Base de données -----
    def creer_table(self):
        self.connexion.execute("""
            CREATE TABLE IF NOT EXISTS etudiants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                age INTEGER NOT NULL,
                note REAL NOT NULL
            )
        """)
        self.connexion.commit()

    def migrer_json(self):
        """Importe l'ancien fichier JSON une seule fois, si la base est vide."""
        nombre = self.connexion.execute("SELECT COUNT(*) FROM etudiants").fetchone()[0]
        if nombre > 0 or not os.path.exists(self.fichier_json):
            return

        with open(self.fichier_json, "r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)

        for d in donnees:
            self.connexion.execute(
                "INSERT INTO etudiants (nom, age, note) VALUES (?, ?, ?)",
                (d["nom"], d["age"], d["note"])
            )
        self.connexion.commit()

    def charger(self):
        curseur = self.connexion.execute("SELECT id, nom, age, note FROM etudiants")
        self.etudiants = []
        for ligne in curseur.fetchall():
            self.etudiants.append(Etudiant(ligne[1], ligne[2], ligne[3], ligne[0]))

    # ----- Gestion de la liste -----
    def ajouter(self, etudiant):
        curseur = self.connexion.execute(
            "INSERT INTO etudiants (nom, age, note) VALUES (?, ?, ?)",
            (etudiant.nom, etudiant.age, etudiant.note)
        )
        self.connexion.commit()
        etudiant.id = curseur.lastrowid
        self.etudiants.append(etudiant)

    def supprimer(self, etudiant):
        self.connexion.execute("DELETE FROM etudiants WHERE id = ?", (etudiant.id,))
        self.connexion.commit()
        self.etudiants.remove(etudiant)

    def modifier(self, etudiant, nom, age, note):
        self.connexion.execute(
            "UPDATE etudiants SET nom = ?, age = ?, note = ? WHERE id = ?",
            (nom, age, note, etudiant.id)
        )
        self.connexion.commit()
        etudiant.nom = nom
        etudiant.age = age
        etudiant.note = note

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