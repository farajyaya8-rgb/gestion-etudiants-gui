class Etudiant:
    def __init__(self, nom, age, note, id_etudiant=None):
        self.nom = nom
        self.age = age
        self.note = note
        self.id = id_etudiant

    def est_admis(self):
        return self.note >= 10

    def initiales(self):
        mots = self.nom.split()
        if len(mots) >= 2:
            return (mots[0][0] + mots[1][0]).upper()
        return self.nom[:2].upper()

    def en_dictionnaire(self):
        return {"nom": self.nom, "age": self.age, "note": self.note}

    @classmethod
    def depuis_dictionnaire(cls, donnees):
        return cls(donnees["nom"], donnees["age"], donnees["note"])