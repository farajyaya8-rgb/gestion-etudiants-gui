import json
import pytest

import gestionnaire as module_gestionnaire
from etudiant import Etudiant
from gestionnaire import GestionnaireEtudiants


@pytest.fixture
def gest(tmp_path, monkeypatch):
    """Un gestionnaire avec une base vide, dans un dossier temporaire."""
    monkeypatch.setattr(module_gestionnaire, "DOSSIER", str(tmp_path))
    return GestionnaireEtudiants()


def relire():
    """Ouvre un nouveau gestionnaire et recharge les étudiants depuis la base."""
    g = GestionnaireEtudiants()
    g.charger()
    return g.etudiants


def remplir(g):
    g.ajouter(Etudiant("Marie Dupont", 20, 15))
    g.ajouter(Etudiant("Karim Benali", 21, 8))
    g.ajouter(Etudiant("Lina Martin", 19, 10))


# ---------- Classe Etudiant ----------
def test_etudiant_sans_id():
    e = Etudiant("Marie Dupont", 20, 15)
    assert e.id is None


def test_est_admis():
    assert Etudiant("A", 20, 15).est_admis() is True
    assert Etudiant("B", 20, 10).est_admis() is True
    assert Etudiant("C", 20, 9.5).est_admis() is False
    assert Etudiant("D", 20, 0).est_admis() is False


def test_initiales():
    assert Etudiant("Marie Dupont", 20, 15).initiales() == "MD"
    assert Etudiant("karim", 20, 15).initiales() == "KA"


def test_dictionnaire_aller_retour():
    e = Etudiant("Marie Dupont", 20, 15)
    copie = Etudiant.depuis_dictionnaire(e.en_dictionnaire())
    assert copie.nom == "Marie Dupont"
    assert copie.age == 20
    assert copie.note == 15


# ---------- Classe GestionnaireEtudiants ----------
def test_ajouter_attribue_un_id(gest):
    e = Etudiant("Marie Dupont", 20, 15)
    gest.ajouter(e)
    assert e.id is not None
    assert len(gest.etudiants) == 1


def test_ajouter_est_conserve(gest):
    gest.ajouter(Etudiant("Marie Dupont", 20, 15))
    etudiants = relire()
    assert len(etudiants) == 1
    assert etudiants[0].nom == "Marie Dupont"
    assert etudiants[0].note == 15


def test_modifier_est_conserve(gest):
    e = Etudiant("Marie Dupont", 20, 15)
    gest.ajouter(e)
    gest.modifier(e, "Marie Durand", 21, 17.5)
    etudiants = relire()
    assert etudiants[0].nom == "Marie Durand"
    assert etudiants[0].age == 21
    assert etudiants[0].note == 17.5


def test_supprimer_est_conserve(gest):
    remplir(gest)
    gest.supprimer(gest.etudiants[0])
    assert len(gest.etudiants) == 2
    assert len(relire()) == 2


def test_nom_existe(gest):
    e = Etudiant("Marie Dupont", 20, 15)
    gest.ajouter(e)
    assert gest.nom_existe("marie dupont") is True
    assert gest.nom_existe("Karim Benali") is False
    assert gest.nom_existe("Marie Dupont", ignorer=e) is False


def test_tri_alphabetique(gest):
    remplir(gest)
    noms = [e.nom for e in gest.obtenir("A-Z")]
    assert noms == ["Karim Benali", "Lina Martin", "Marie Dupont"]


def test_tri_par_note(gest):
    remplir(gest)
    noms = [e.nom for e in gest.obtenir("Meilleures notes")]
    assert noms == ["Marie Dupont", "Lina Martin", "Karim Benali"]


def test_filtre_admis_et_ajournes(gest):
    remplir(gest)
    assert len(gest.obtenir(filtre="Admis")) == 2
    ajournes = gest.obtenir(filtre="Ajournés")
    assert len(ajournes) == 1
    assert ajournes[0].nom == "Karim Benali"


def test_recherche(gest):
    remplir(gest)
    resultats = gest.obtenir(recherche="MARIE")
    assert len(resultats) == 1
    assert resultats[0].nom == "Marie Dupont"


def test_statistiques_liste_vide(gest):
    assert gest.statistiques() is None


def test_statistiques(gest):
    remplir(gest)
    stats = gest.statistiques()
    assert stats["nombre"] == 3
    assert stats["moyenne"] == pytest.approx(11)
    assert stats["admis"] == 2
    assert stats["ajournes"] == 1
    assert stats["repartition"] == [0, 1, 1, 1]
    assert stats["meilleurs"][0].nom == "Marie Dupont"


# ---------- Import de l'ancien JSON ----------
def test_migration_json(tmp_path, monkeypatch):
    monkeypatch.setattr(module_gestionnaire, "DOSSIER", str(tmp_path))
    donnees = [
        {"nom": "Marie Dupont", "age": 20, "note": 15},
        {"nom": "Karim Benali", "age": 21, "note": 8},
    ]
    (tmp_path / "etudiants.json").write_text(json.dumps(donnees), encoding="utf-8")

    g = GestionnaireEtudiants()
    g.charger()
    assert len(g.etudiants) == 2


def test_migration_une_seule_fois(tmp_path, monkeypatch):
    monkeypatch.setattr(module_gestionnaire, "DOSSIER", str(tmp_path))
    donnees = [{"nom": "Marie Dupont", "age": 20, "note": 15}]
    (tmp_path / "etudiants.json").write_text(json.dumps(donnees), encoding="utf-8")

    GestionnaireEtudiants()
    g = GestionnaireEtudiants()
    g.charger()
    assert len(g.etudiants) == 1