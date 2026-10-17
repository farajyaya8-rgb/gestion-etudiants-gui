import json
import math
import os
from datetime import datetime
import customtkinter as ctk

try:
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL = True
except ImportError:
    MPL = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Le fichier JSON est toujours cherché à côté de ce fichier .py
DOSSIER = os.path.dirname(os.path.abspath(__file__))
FICHIER = os.path.join(DOSSIER, "etudiants.json")

etudiants = []
selection = {"etudiant": None}
cartes_liste = []
filtres = {"tri": "A-Z", "filtre": "Tous"}
timer_toast = {"id": None}

CARTE_NORMALE = ("#f5f5f5", "#363636")
CARTE_SURVOL = ("#e0e0e0", "#454545")
CARTE_SELECTION = ("#a9cce3", "#1f538d")


# ---------- Fichier JSON ----------
def sauvegarder_etudiants():
    with open(FICHIER, "w", encoding="utf-8") as fichier:
        json.dump(etudiants, fichier, indent=4, ensure_ascii=False)


def charger_etudiants():
    global etudiants
    try:
        with open(FICHIER, "r", encoding="utf-8") as fichier:
            etudiants = json.load(fichier)
    except FileNotFoundError:
        etudiants = []


# ---------- Petites fonctions utiles ----------
def cle_note(etudiant):
    return etudiant["note"]


def cle_nom(etudiant):
    return etudiant["nom"].lower()


def format_note(note):
    """14 -> '14' ; 14.5 -> '14,5'"""
    return f"{note:g}".replace(".", ",")


def initiales(nom):
    mots = nom.split()
    if len(mots) >= 2:
        return (mots[0][0] + mots[1][0]).upper()
    return nom[:2].upper()


def couleur_avatar(nom):
    palette = ["#3498db", "#9b59b6", "#e67e22", "#1abc9c", "#e84393", "#16a085"]
    total = 0
    for lettre in nom:
        total = total + ord(lettre)
    return palette[total % len(palette)]


def trouver_index(etudiant):
    for i, e in enumerate(etudiants):
        if e is etudiant:
            return i
    return None


def nom_existe(nom, ignorer=None):
    """True si un autre étudiant porte déjà ce nom."""
    for e in etudiants:
        if e is not ignorer and e["nom"].lower() == nom.lower():
            return True
    return False


def vider_champs():
    entree_nom.delete(0, "end")
    entree_age.delete(0, "end")
    entree_note.delete(0, "end")


# ---------- Notifications ----------
def cacher_toast():
    toast.place_forget()
    timer_toast["id"] = None


def notifier(message, genre="succes"):
    couleurs = {
        "succes": "#27ae60",
        "erreur": "#c0392b",
        "attention": "#e67e22",
    }
    toast.configure(text="   " + message + "   ", fg_color=couleurs[genre])
    toast.place(relx=0.58, rely=0.03, anchor="n")
    if timer_toast["id"] is not None:
        fenetre.after_cancel(timer_toast["id"])
    timer_toast["id"] = fenetre.after(2500, cacher_toast)


# ---------- Fenêtre de confirmation (même style que l'application) ----------
def confirmer(titre, message):
    resultat = {"ok": False}

    largeur = 420
    hauteur = 190
    fenetre.update_idletasks()
    x = fenetre.winfo_x() + (fenetre.winfo_width() - largeur) // 2
    y = fenetre.winfo_y() + (fenetre.winfo_height() - hauteur) // 2

    boite = ctk.CTkToplevel(fenetre)
    boite.title(titre)
    boite.geometry(f"{largeur}x{hauteur}+{x}+{y}")
    boite.resizable(False, False)
    boite.transient(fenetre)

    ctk.CTkLabel(boite, text=message, wraplength=360, font=ctk.CTkFont(size=15)).pack(pady=(35, 25), padx=20)

    def oui():
        resultat["ok"] = True
        boite.destroy()

    def non():
        boite.destroy()

    cadre = ctk.CTkFrame(boite, fg_color="transparent")
    cadre.pack()
    ctk.CTkButton(cadre, text="Oui", width=120, fg_color="#c0392b", hover_color="#962d22", command=oui).pack(side="left", padx=10)
    ctk.CTkButton(cadre, text="Non", width=120, fg_color="#7f8c8d", hover_color="#626d6e", command=non).pack(side="left", padx=10)

    boite.after(150, boite.grab_set)
    boite.after(150, boite.focus)
    fenetre.wait_window(boite)
    return resultat["ok"]


# ---------- Lecture et validation des champs ----------
def lire_champs():
    """Retourne (nom, age, note) si tout est valide, sinon None."""
    nom = entree_nom.get().strip()
    if nom == "":
        notifier("Nom invalide", "erreur")
        return None

    texte_note = entree_note.get().strip().replace(",", ".")
    try:
        age = int(entree_age.get())
        note = float(texte_note)
    except ValueError:
        notifier("Age : nombre entier. Note : nombre", "erreur")
        return None

    if not math.isfinite(note):
        notifier("Note invalide", "erreur")
        return None
    if age <= 0:
        notifier("Age invalide", "erreur")
        return None
    if note < 0 or note > 20:
        notifier("La note doit être entre 0 et 20", "erreur")
        return None

    note = round(note, 2)
    if note == int(note):
        note = int(note)

    return nom, age, note


# ---------- Cartes d'étudiants ----------
def creer_carte(parent, etudiant, selectable):
    carte = ctk.CTkFrame(parent, corner_radius=12, fg_color=CARTE_NORMALE)
    carte.pack(fill="x", padx=6, pady=4)

    pastille = ctk.CTkLabel(
        carte,
        text=initiales(etudiant["nom"]),
        width=44,
        height=44,
        corner_radius=22,
        fg_color=couleur_avatar(etudiant["nom"]),
        text_color="white",
        font=ctk.CTkFont(size=15, weight="bold"),
    )
    pastille.pack(side="left", padx=12, pady=10)

    infos = ctk.CTkFrame(carte, fg_color="transparent")
    infos.pack(side="left", pady=8)

    label_nom = ctk.CTkLabel(infos, text=etudiant["nom"], font=ctk.CTkFont(size=16, weight="bold"))
    label_nom.pack(anchor="w")
    label_age = ctk.CTkLabel(infos, text=f"{etudiant['age']} ans", text_color="gray")
    label_age.pack(anchor="w")

    if etudiant["note"] >= 10:
        couleur_badge = "#27ae60"
        statut = "Admis"
    else:
        couleur_badge = "#c0392b"
        statut = "Ajourné"

    badge = ctk.CTkLabel(
        carte,
        text=f"{format_note(etudiant['note'])}/20",
        width=80,
        height=32,
        corner_radius=16,
        fg_color=couleur_badge,
        text_color="white",
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    badge.pack(side="right", padx=15)

    label_statut = ctk.CTkLabel(carte, text=statut, text_color="gray")
    label_statut.pack(side="right", padx=5)

    def entrer(event=None):
        if not (selectable and selection["etudiant"] is etudiant):
            carte.configure(fg_color=CARTE_SURVOL)

    def sortir(event=None):
        if selectable and selection["etudiant"] is etudiant:
            carte.configure(fg_color=CARTE_SELECTION)
        else:
            carte.configure(fg_color=CARTE_NORMALE)

    def cliquer(event=None):
        if selectable:
            selectionner(etudiant)

    widgets = [carte, pastille, infos, label_nom, label_age, badge, label_statut]
    for widget in widgets:
        widget.bind("<Enter>", entrer)
        widget.bind("<Leave>", sortir)
        widget.bind("<Button-1>", cliquer)

    return carte


def colorer_cartes():
    for etudiant, carte in cartes_liste:
        if etudiant is selection["etudiant"]:
            carte.configure(fg_color=CARTE_SELECTION)
        else:
            carte.configure(fg_color=CARTE_NORMALE)


def selectionner(etudiant):
    selection["etudiant"] = etudiant
    vider_champs()
    entree_nom.insert(0, etudiant["nom"])
    entree_age.insert(0, str(etudiant["age"]))
    entree_note.insert(0, format_note(etudiant["note"]))
    colorer_cartes()


# ---------- Tri et filtres ----------
def obtenir_etudiants_affiches():
    resultat = []
    for etudiant in etudiants:
        if filtres["filtre"] == "Admis" and etudiant["note"] < 10:
            continue
        if filtres["filtre"] == "Ajournés" and etudiant["note"] >= 10:
            continue
        resultat.append(etudiant)

    if filtres["tri"] == "A-Z":
        resultat.sort(key=cle_nom)
    else:
        resultat.sort(key=cle_note, reverse=True)
    return resultat


def changer_tri(valeur):
    filtres["tri"] = valeur
    rafraichir_liste()


def changer_filtre(valeur):
    filtres["filtre"] = valeur
    rafraichir_liste()


# ---------- Graphiques ----------
def dessiner_graphiques():
    if not MPL:
        return

    sombre = ctk.get_appearance_mode() == "Dark"
    fond = "#2b2b2b" if sombre else "#dbdbdb"
    texte = "white" if sombre else "black"

    figure.set_facecolor(fond)
    for axe in (axe_notes, axe_reussite):
        axe.clear()
        axe.axis("on")
        axe.set_facecolor(fond)

    compte = [0, 0, 0, 0]
    admis = 0
    for etudiant in etudiants:
        note = etudiant["note"]
        if note < 5:
            compte[0] = compte[0] + 1
        elif note < 10:
            compte[1] = compte[1] + 1
        elif note < 15:
            compte[2] = compte[2] + 1
        else:
            compte[3] = compte[3] + 1
        if note >= 10:
            admis = admis + 1
    ajournes = len(etudiants) - admis

    axe_notes.bar(["0-5", "5-10", "10-15", "15-20"], compte, color=["#e74c3c", "#e67e22", "#3498db", "#2ecc71"])
    axe_notes.set_title("Répartition des notes", color=texte, fontsize=11)
    axe_notes.tick_params(colors=texte)
    axe_notes.yaxis.set_major_locator(MaxNLocator(integer=True))
    for cote in ["top", "right"]:
        axe_notes.spines[cote].set_visible(False)
    for cote in ["left", "bottom"]:
        axe_notes.spines[cote].set_color(texte)

    axe_reussite.set_title("Admis / Ajournés", color=texte, fontsize=11)
    if len(etudiants) == 0:
        axe_reussite.text(0.5, 0.5, "Pas de données", ha="center", va="center",
                          color=texte, transform=axe_reussite.transAxes)
        axe_reussite.axis("off")
    else:
        valeurs = []
        noms = []
        couleurs = []
        if admis > 0:
            valeurs.append(admis)
            noms.append("Admis")
            couleurs.append("#2ecc71")
        if ajournes > 0:
            valeurs.append(ajournes)
            noms.append("Ajournés")
            couleurs.append("#e74c3c")
        axe_reussite.pie(valeurs, labels=noms, colors=couleurs,
                         autopct="%1.0f%%", textprops={"color": texte})

    figure.tight_layout()
    canvas_graphiques.draw()


# ---------- Navigation et apparence ----------
def afficher_page(nom):
    for page in pages.values():
        page.pack_forget()
    pages[nom].pack(fill="both", expand=True)

    for nom_bouton, bouton in boutons_menu.items():
        if nom_bouton == nom:
            bouton.configure(fg_color=("#3a7ebf", "#1f538d"), text_color="white")
        else:
            bouton.configure(fg_color="transparent", text_color=("gray10", "gray90"))


def changer_mode(choix):
    if choix == "Clair":
        ctk.set_appearance_mode("light")
    else:
        ctk.set_appearance_mode("dark")
    dessiner_graphiques()


# ---------- Rafraîchissement ----------
def vider_conteneur(conteneur):
    for widget in conteneur.winfo_children():
        widget.destroy()


def rafraichir_liste():
    vider_conteneur(conteneur_liste)
    cartes_liste.clear()

    affiches = obtenir_etudiants_affiches()
    if len(affiches) == 0:
        ctk.CTkLabel(conteneur_liste, text="Aucun étudiant à afficher.", text_color="gray").pack(pady=30)
        return

    for etudiant in affiches:
        carte = creer_carte(conteneur_liste, etudiant, True)
        cartes_liste.append((etudiant, carte))
    colorer_cartes()


def rafraichir_recherche(event=None):
    texte = entree_recherche.get().strip().lower()
    vider_conteneur(conteneur_recherche)

    compte = 0
    for etudiant in sorted(etudiants, key=cle_nom):
        if texte in etudiant["nom"].lower():
            creer_carte(conteneur_recherche, etudiant, False)
            compte = compte + 1

    label_resultats.configure(text=f"{compte} résultat(s)")


def rafraichir_accueil():
    nombre = len(etudiants)

    if nombre == 0:
        cartes["nombre"].configure(text="0")
        cartes["moyenne"].configure(text="-")
        cartes["admis"].configure(text="0")
        cartes["ajournes"].configure(text="0")
        barre_taux.set(0)
        label_taux.configure(text="Taux de réussite : -")
        for label in podium_labels:
            label.configure(text="-")
        dessiner_graphiques()
        return

    somme = 0
    admis = 0
    for etudiant in etudiants:
        somme = somme + etudiant["note"]
        if etudiant["note"] >= 10:
            admis = admis + 1
    moyenne = somme / nombre
    ajournes = nombre - admis
    taux = admis / nombre

    cartes["nombre"].configure(text=str(nombre))
    cartes["moyenne"].configure(text=f"{moyenne:.1f}".replace(".", ","))
    cartes["admis"].configure(text=str(admis))
    cartes["ajournes"].configure(text=str(ajournes))

    barre_taux.set(taux)
    label_taux.configure(text=f"Taux de réussite : {taux * 100:.0f} %")

    medailles = ["🥇", "🥈", "🥉"]
    meilleurs = sorted(etudiants, key=cle_note, reverse=True)[:3]
    for i in range(3):
        if i < len(meilleurs):
            podium_labels[i].configure(
                text=f"{medailles[i]}  {meilleurs[i]['nom']}  -  {format_note(meilleurs[i]['note'])}/20"
            )
        else:
            podium_labels[i].configure(text="-")

    dessiner_graphiques()


def rafraichir_tout():
    rafraichir_liste()
    rafraichir_recherche()
    rafraichir_accueil()


# ---------- Actions ----------
def ajouter():
    resultat = lire_champs()
    if resultat is None:
        return
    nom, age, note = resultat

    if nom_existe(nom):
        if not confirmer("Doublon", f"Un étudiant nommé {nom} existe déjà. L'ajouter quand même ?"):
            return

    etudiants.append({"nom": nom, "age": age, "note": note})
    sauvegarder_etudiants()
    selection["etudiant"] = None
    vider_champs()
    rafraichir_tout()
    notifier("Etudiant ajouté !")


def modifier():
    etudiant = selection["etudiant"]
    if etudiant is None:
        notifier("Sélectionne un étudiant dans la liste", "attention")
        return

    resultat = lire_champs()
    if resultat is None:
        return
    nom, age, note = resultat

    if nom_existe(nom, ignorer=etudiant):
        if not confirmer("Doublon", f"Un autre étudiant s'appelle déjà {nom}. Modifier quand même ?"):
            return

    etudiant["nom"] = nom
    etudiant["age"] = age
    etudiant["note"] = note
    sauvegarder_etudiants()
    selection["etudiant"] = None
    vider_champs()
    rafraichir_tout()
    notifier("Etudiant modifié !")


def supprimer():
    etudiant = selection["etudiant"]
    if etudiant is None:
        notifier("Sélectionne un étudiant dans la liste", "attention")
        return

    if not confirmer("Confirmation", f"Voulez-vous vraiment supprimer {etudiant['nom']} ?"):
        return

    etudiants.pop(trouver_index(etudiant))
    sauvegarder_etudiants()
    selection["etudiant"] = None
    vider_champs()
    rafraichir_tout()
    notifier("Etudiant supprimé !", "erreur")


def annuler():
    """Désélectionne l'étudiant et vide les champs."""
    selection["etudiant"] = None
    vider_champs()
    colorer_cartes()
    fenetre.focus()


def aller_ajouter():
    afficher_page("Étudiants")
    entree_nom.focus()


# ---------- Fenêtre ----------
charger_etudiants()

fenetre = ctk.CTk()
fenetre.title("Gestion des étudiants")
fenetre.geometry("1150x720")
fenetre.minsize(1000, 650)

# ---------- Menu latéral ----------
menu = ctk.CTkFrame(fenetre, width=200, corner_radius=0)
menu.pack(side="left", fill="y")
menu.pack_propagate(False)

ctk.CTkLabel(menu, text="🎓 Etudiants", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 2))
ctk.CTkLabel(menu, text="Gestion & suivi", text_color="gray").pack(pady=(0, 30))

boutons_menu = {}
elements_menu = [("Accueil", "🏠"), ("Étudiants", "👥"), ("Recherche", "🔍")]
for nom_page, icone in elements_menu:
    bouton = ctk.CTkButton(
        menu,
        text=f"{icone}   {nom_page}",
        height=42,
        anchor="w",
        fg_color="transparent",
        font=ctk.CTkFont(size=15),
        command=lambda n=nom_page: afficher_page(n),
    )
    bouton.pack(fill="x", padx=15, pady=5)
    boutons_menu[nom_page] = bouton

ctk.CTkOptionMenu(menu, values=["Sombre", "Clair"], command=changer_mode).pack(side="bottom", pady=(0, 25))
ctk.CTkLabel(menu, text="Apparence :", text_color="gray").pack(side="bottom", pady=(0, 5))

# ---------- Zone de contenu ----------
contenu = ctk.CTkFrame(fenetre, fg_color="transparent")
contenu.pack(side="right", fill="both", expand=True, padx=20, pady=20)

page_accueil = ctk.CTkFrame(contenu, fg_color="transparent")
page_etudiants = ctk.CTkFrame(contenu, fg_color="transparent")
page_recherche = ctk.CTkFrame(contenu, fg_color="transparent")

pages = {
    "Accueil": page_accueil,
    "Étudiants": page_etudiants,
    "Recherche": page_recherche,
}

toast = ctk.CTkLabel(fenetre, text="", height=42, corner_radius=12,
                     text_color="white", font=ctk.CTkFont(size=14, weight="bold"))

# ----- Page Accueil -----
salut = "Bonjour" if datetime.now().hour < 18 else "Bonsoir"
ctk.CTkLabel(page_accueil, text=f"{salut} !", font=ctk.CTkFont(size=34, weight="bold")).pack(anchor="w", padx=20, pady=(5, 0))
ctk.CTkLabel(page_accueil, text="Voici un résumé de votre classe.", text_color="gray",
             font=ctk.CTkFont(size=15)).pack(anchor="w", padx=20, pady=(0, 10))

cartes = {}
cadre_cartes = ctk.CTkFrame(page_accueil, fg_color="transparent")
cadre_cartes.pack(fill="x", padx=12, pady=5)

elements_cartes = [
    ("nombre", "Etudiants", "#3498db"),
    ("moyenne", "Moyenne /20", "#9b59b6"),
    ("admis", "Admis", "#2ecc71"),
    ("ajournes", "Ajournés", "#e74c3c"),
]

for colonne, (cle, titre_carte, couleur) in enumerate(elements_cartes):
    cadre_cartes.columnconfigure(colonne, weight=1)
    carte_stat = ctk.CTkFrame(cadre_cartes, corner_radius=15)
    carte_stat.grid(row=0, column=colonne, padx=8, sticky="ew")

    valeur = ctk.CTkLabel(carte_stat, text="0", font=ctk.CTkFont(size=32, weight="bold"), text_color=couleur)
    valeur.pack(pady=(14, 0))
    ctk.CTkLabel(carte_stat, text=titre_carte, text_color="gray").pack(pady=(0, 14))
    cartes[cle] = valeur

cadre_taux = ctk.CTkFrame(page_accueil, corner_radius=15)
cadre_taux.pack(fill="x", padx=20, pady=10)

label_taux = ctk.CTkLabel(cadre_taux, text="Taux de réussite : -", font=ctk.CTkFont(size=15, weight="bold"))
label_taux.pack(anchor="w", padx=20, pady=(12, 5))

barre_taux = ctk.CTkProgressBar(cadre_taux, height=14, progress_color="#2ecc71")
barre_taux.pack(fill="x", padx=20, pady=(0, 12))
barre_taux.set(0)

cadre_milieu = ctk.CTkFrame(page_accueil, fg_color="transparent")
cadre_milieu.pack(fill="both", expand=True, padx=20, pady=5)

cadre_graphiques = ctk.CTkFrame(cadre_milieu, corner_radius=15)
cadre_graphiques.pack(side="left", fill="both", expand=True, padx=(0, 10))

if MPL:
    figure = Figure(figsize=(6, 2.8), dpi=100)
    axe_notes, axe_reussite = figure.subplots(1, 2)
    canvas_graphiques = FigureCanvasTkAgg(figure, master=cadre_graphiques)
    canvas_graphiques.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
else:
    ctk.CTkLabel(cadre_graphiques, text="Pour voir les graphiques :\npip install matplotlib",
                 text_color="gray").pack(expand=True)

cadre_podium = ctk.CTkFrame(cadre_milieu, corner_radius=15, width=300)
cadre_podium.pack(side="right", fill="y")
cadre_podium.pack_propagate(False)

ctk.CTkLabel(cadre_podium, text="Top 3 des étudiants", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

podium_labels = []
for i in range(3):
    label = ctk.CTkLabel(cadre_podium, text="-", font=ctk.CTkFont(size=15))
    label.pack(anchor="w", padx=25, pady=6)
    podium_labels.append(label)

cadre_rapide = ctk.CTkFrame(page_accueil, fg_color="transparent")
cadre_rapide.pack(pady=10)

ctk.CTkButton(cadre_rapide, text="➕  Ajouter un étudiant", width=200, height=40,
              command=aller_ajouter).pack(side="left", padx=10)
ctk.CTkButton(cadre_rapide, text="🔍  Rechercher", width=200, height=40, fg_color="#8e44ad",
              hover_color="#6c3483", command=lambda: afficher_page("Recherche")).pack(side="left", padx=10)

# ----- Page Étudiants -----
ctk.CTkLabel(page_etudiants, text="Gestion des étudiants",
             font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", padx=20, pady=(5, 10))

formulaire = ctk.CTkFrame(page_etudiants)
formulaire.pack(fill="x", padx=10, pady=5)

entree_nom = ctk.CTkEntry(formulaire, placeholder_text="Nom", width=250)
entree_nom.pack(side="left", padx=10, pady=12)

entree_age = ctk.CTkEntry(formulaire, placeholder_text="Age", width=100)
entree_age.pack(side="left", padx=10, pady=12)

entree_note = ctk.CTkEntry(formulaire, placeholder_text="Note /20", width=100)
entree_note.pack(side="left", padx=10, pady=12)

cadre_boutons = ctk.CTkFrame(page_etudiants, fg_color="transparent")
cadre_boutons.pack(pady=5)

ctk.CTkButton(cadre_boutons, text="Ajouter", width=120, fg_color="#27ae60",
              hover_color="#1e8449", command=ajouter).pack(side="left", padx=6)
ctk.CTkButton(cadre_boutons, text="Modifier", width=120, fg_color="#e67e22",
              hover_color="#b9651b", command=modifier).pack(side="left", padx=6)
ctk.CTkButton(cadre_boutons, text="Supprimer", width=120, fg_color="#c0392b",
              hover_color="#962d22", command=supprimer).pack(side="left", padx=6)
ctk.CTkButton(cadre_boutons, text="Annuler", width=120, fg_color="#7f8c8d",
              hover_color="#626d6e", command=annuler).pack(side="left", padx=6)

barre_outils = ctk.CTkFrame(page_etudiants, fg_color="transparent")
barre_outils.pack(fill="x", padx=10, pady=(10, 0))

ctk.CTkLabel(barre_outils, text="Trier :").pack(side="left", padx=(5, 5))
segment_tri = ctk.CTkSegmentedButton(barre_outils, values=["A-Z", "Meilleures notes"], command=changer_tri)
segment_tri.pack(side="left")
segment_tri.set("A-Z")

ctk.CTkLabel(barre_outils, text="Afficher :").pack(side="left", padx=(25, 5))
segment_filtre = ctk.CTkSegmentedButton(barre_outils, values=["Tous", "Admis", "Ajournés"], command=changer_filtre)
segment_filtre.pack(side="left")
segment_filtre.set("Tous")

conteneur_liste = ctk.CTkScrollableFrame(page_etudiants)
conteneur_liste.pack(fill="both", expand=True, padx=10, pady=10)

# ----- Page Recherche -----
ctk.CTkLabel(page_recherche, text="Recherche", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", padx=20, pady=(5, 10))

entree_recherche = ctk.CTkEntry(page_recherche, placeholder_text="Tape un nom pour rechercher...", width=400)
entree_recherche.pack(pady=(10, 5))
entree_recherche.bind("<KeyRelease>", rafraichir_recherche)

label_resultats = ctk.CTkLabel(page_recherche, text="", text_color="gray")
label_resultats.pack()

conteneur_recherche = ctk.CTkScrollableFrame(page_recherche)
conteneur_recherche.pack(fill="both", expand=True, padx=10, pady=10)

# ---------- Démarrage ----------
rafraichir_tout()
afficher_page("Accueil")

fenetre.mainloop()