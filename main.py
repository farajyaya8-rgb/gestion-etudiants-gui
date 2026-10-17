import math
from datetime import datetime
import customtkinter as ctk

from etudiant import Etudiant
from gestionnaire import GestionnaireEtudiants

try:
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL = True
except ImportError:
    MPL = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CARTE_NORMALE = ("#f5f5f5", "#363636")
CARTE_SURVOL = ("#e0e0e0", "#454545")
CARTE_SELECTION = ("#a9cce3", "#1f538d")


def format_note(note):
    """14 -> '14' ; 14.5 -> '14,5'"""
    return f"{note:g}".replace(".", ",")


def couleur_avatar(nom):
    palette = ["#3498db", "#9b59b6", "#e67e22", "#1abc9c", "#e84393", "#16a085"]
    total = 0
    for lettre in nom:
        total = total + ord(lettre)
    return palette[total % len(palette)]


class Application(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.gestionnaire = GestionnaireEtudiants()
        self.gestionnaire.charger()

        self.etudiant_selectionne = None
        self.cartes_liste = []
        self.filtres = {"tri": "A-Z", "filtre": "Tous"}
        self.timer_toast = None

        self.title("Gestion des étudiants")
        self.geometry("1150x720")
        self.minsize(1000, 650)

        self.creer_menu()
        self.creer_contenu()
        self.creer_page_accueil()
        self.creer_page_etudiants()
        self.creer_page_recherche()

        self.rafraichir_tout()
        self.afficher_page("Accueil")

    # ---------- Construction de l'interface ----------
    def creer_menu(self):
        menu = ctk.CTkFrame(self, width=200, corner_radius=0)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)

        ctk.CTkLabel(menu, text="🎓 Etudiants", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 2))
        ctk.CTkLabel(menu, text="Gestion & suivi", text_color="gray").pack(pady=(0, 30))

        self.boutons_menu = {}
        elements_menu = [("Accueil", "🏠"), ("Étudiants", "👥"), ("Recherche", "🔍")]
        for nom_page, icone in elements_menu:
            bouton = ctk.CTkButton(
                menu,
                text=f"{icone}   {nom_page}",
                height=42,
                anchor="w",
                fg_color="transparent",
                font=ctk.CTkFont(size=15),
                command=lambda n=nom_page: self.afficher_page(n),
            )
            bouton.pack(fill="x", padx=15, pady=5)
            self.boutons_menu[nom_page] = bouton

        ctk.CTkOptionMenu(menu, values=["Sombre", "Clair"], command=self.changer_mode).pack(side="bottom", pady=(0, 25))
        ctk.CTkLabel(menu, text="Apparence :", text_color="gray").pack(side="bottom", pady=(0, 5))

    def creer_contenu(self):
        contenu = ctk.CTkFrame(self, fg_color="transparent")
        contenu.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.page_accueil = ctk.CTkFrame(contenu, fg_color="transparent")
        self.page_etudiants = ctk.CTkFrame(contenu, fg_color="transparent")
        self.page_recherche = ctk.CTkFrame(contenu, fg_color="transparent")

        self.pages = {
            "Accueil": self.page_accueil,
            "Étudiants": self.page_etudiants,
            "Recherche": self.page_recherche,
        }

        # Créée après le contenu pour rester au-dessus
        self.toast = ctk.CTkLabel(self, text="", height=42, corner_radius=12,
                                  text_color="white", font=ctk.CTkFont(size=14, weight="bold"))

    def creer_page_accueil(self):
        page = self.page_accueil

        salut = "Bonjour" if datetime.now().hour < 18 else "Bonsoir"
        ctk.CTkLabel(page, text=f"{salut} !", font=ctk.CTkFont(size=34, weight="bold")).pack(anchor="w", padx=20, pady=(5, 0))
        ctk.CTkLabel(page, text="Voici un résumé de votre classe.", text_color="gray",
                     font=ctk.CTkFont(size=15)).pack(anchor="w", padx=20, pady=(0, 10))

        self.cartes_stats = {}
        cadre_cartes = ctk.CTkFrame(page, fg_color="transparent")
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
            self.cartes_stats[cle] = valeur

        cadre_taux = ctk.CTkFrame(page, corner_radius=15)
        cadre_taux.pack(fill="x", padx=20, pady=10)

        self.label_taux = ctk.CTkLabel(cadre_taux, text="Taux de réussite : -", font=ctk.CTkFont(size=15, weight="bold"))
        self.label_taux.pack(anchor="w", padx=20, pady=(12, 5))

        self.barre_taux = ctk.CTkProgressBar(cadre_taux, height=14, progress_color="#2ecc71")
        self.barre_taux.pack(fill="x", padx=20, pady=(0, 12))
        self.barre_taux.set(0)

        cadre_milieu = ctk.CTkFrame(page, fg_color="transparent")
        cadre_milieu.pack(fill="both", expand=True, padx=20, pady=5)

        cadre_graphiques = ctk.CTkFrame(cadre_milieu, corner_radius=15)
        cadre_graphiques.pack(side="left", fill="both", expand=True, padx=(0, 10))

        if MPL:
            self.figure = Figure(figsize=(6, 2.8), dpi=100)
            self.axe_notes, self.axe_reussite = self.figure.subplots(1, 2)
            self.canvas_graphiques = FigureCanvasTkAgg(self.figure, master=cadre_graphiques)
            self.canvas_graphiques.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        else:
            ctk.CTkLabel(cadre_graphiques, text="Pour voir les graphiques :\npip install matplotlib",
                         text_color="gray").pack(expand=True)

        cadre_podium = ctk.CTkFrame(cadre_milieu, corner_radius=15, width=300)
        cadre_podium.pack(side="right", fill="y")
        cadre_podium.pack_propagate(False)

        ctk.CTkLabel(cadre_podium, text="Top 3 des étudiants",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        self.podium_labels = []
        for i in range(3):
            label = ctk.CTkLabel(cadre_podium, text="-", font=ctk.CTkFont(size=15))
            label.pack(anchor="w", padx=25, pady=6)
            self.podium_labels.append(label)

        cadre_rapide = ctk.CTkFrame(page, fg_color="transparent")
        cadre_rapide.pack(pady=10)

        ctk.CTkButton(cadre_rapide, text="➕  Ajouter un étudiant", width=200, height=40,
                      command=self.aller_ajouter).pack(side="left", padx=10)
        ctk.CTkButton(cadre_rapide, text="🔍  Rechercher", width=200, height=40, fg_color="#8e44ad",
                      hover_color="#6c3483", command=lambda: self.afficher_page("Recherche")).pack(side="left", padx=10)

    def creer_page_etudiants(self):
        page = self.page_etudiants

        ctk.CTkLabel(page, text="Gestion des étudiants",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", padx=20, pady=(5, 10))

        formulaire = ctk.CTkFrame(page)
        formulaire.pack(fill="x", padx=10, pady=5)

        self.entree_nom = ctk.CTkEntry(formulaire, placeholder_text="Nom", width=250)
        self.entree_nom.pack(side="left", padx=10, pady=12)

        self.entree_age = ctk.CTkEntry(formulaire, placeholder_text="Age", width=100)
        self.entree_age.pack(side="left", padx=10, pady=12)

        self.entree_note = ctk.CTkEntry(formulaire, placeholder_text="Note /20", width=100)
        self.entree_note.pack(side="left", padx=10, pady=12)

        cadre_boutons = ctk.CTkFrame(page, fg_color="transparent")
        cadre_boutons.pack(pady=5)

        ctk.CTkButton(cadre_boutons, text="Ajouter", width=120, fg_color="#27ae60",
                      hover_color="#1e8449", command=self.ajouter).pack(side="left", padx=6)
        ctk.CTkButton(cadre_boutons, text="Modifier", width=120, fg_color="#e67e22",
                      hover_color="#b9651b", command=self.modifier).pack(side="left", padx=6)
        ctk.CTkButton(cadre_boutons, text="Supprimer", width=120, fg_color="#c0392b",
                      hover_color="#962d22", command=self.supprimer).pack(side="left", padx=6)
        ctk.CTkButton(cadre_boutons, text="Annuler", width=120, fg_color="#7f8c8d",
                      hover_color="#626d6e", command=self.annuler).pack(side="left", padx=6)

        barre_outils = ctk.CTkFrame(page, fg_color="transparent")
        barre_outils.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkLabel(barre_outils, text="Trier :").pack(side="left", padx=(5, 5))
        self.segment_tri = ctk.CTkSegmentedButton(barre_outils, values=["A-Z", "Meilleures notes"],
                                                  command=self.changer_tri)
        self.segment_tri.pack(side="left")
        self.segment_tri.set("A-Z")

        ctk.CTkLabel(barre_outils, text="Afficher :").pack(side="left", padx=(25, 5))
        self.segment_filtre = ctk.CTkSegmentedButton(barre_outils, values=["Tous", "Admis", "Ajournés"],
                                                     command=self.changer_filtre)
        self.segment_filtre.pack(side="left")
        self.segment_filtre.set("Tous")

        self.conteneur_liste = ctk.CTkScrollableFrame(page)
        self.conteneur_liste.pack(fill="both", expand=True, padx=10, pady=10)

    def creer_page_recherche(self):
        page = self.page_recherche

        ctk.CTkLabel(page, text="Recherche", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", padx=20, pady=(5, 10))

        self.entree_recherche = ctk.CTkEntry(page, placeholder_text="Tape un nom pour rechercher...", width=400)
        self.entree_recherche.pack(pady=(10, 5))
        self.entree_recherche.bind("<KeyRelease>", self.rafraichir_recherche)

        self.label_resultats = ctk.CTkLabel(page, text="", text_color="gray")
        self.label_resultats.pack()

        self.conteneur_recherche = ctk.CTkScrollableFrame(page)
        self.conteneur_recherche.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- Navigation et apparence ----------
    def afficher_page(self, nom):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[nom].pack(fill="both", expand=True)

        for nom_bouton, bouton in self.boutons_menu.items():
            if nom_bouton == nom:
                bouton.configure(fg_color=("#3a7ebf", "#1f538d"), text_color="white")
            else:
                bouton.configure(fg_color="transparent", text_color=("gray10", "gray90"))

    def changer_mode(self, choix):
        if choix == "Clair":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
        self.dessiner_graphiques(self.gestionnaire.statistiques())

    # ---------- Notifications et confirmation ----------
    def cacher_toast(self):
        self.toast.place_forget()
        self.timer_toast = None

    def notifier(self, message, genre="succes"):
        couleurs = {
            "succes": "#27ae60",
            "erreur": "#c0392b",
            "attention": "#e67e22",
        }
        self.toast.configure(text="   " + message + "   ", fg_color=couleurs[genre])
        self.toast.place(relx=0.58, rely=0.03, anchor="n")
        if self.timer_toast is not None:
            self.after_cancel(self.timer_toast)
        self.timer_toast = self.after(2500, self.cacher_toast)

    def confirmer(self, titre, message):
        resultat = {"ok": False}

        largeur = 420
        hauteur = 190
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - largeur) // 2
        y = self.winfo_y() + (self.winfo_height() - hauteur) // 2

        boite = ctk.CTkToplevel(self)
        boite.title(titre)
        boite.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        boite.resizable(False, False)
        boite.transient(self)

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
        self.wait_window(boite)
        return resultat["ok"]

    # ---------- Champs du formulaire ----------
    def vider_champs(self):
        self.entree_nom.delete(0, "end")
        self.entree_age.delete(0, "end")
        self.entree_note.delete(0, "end")

    def lire_champs(self):
        """Retourne (nom, age, note) si tout est valide, sinon None."""
        nom = self.entree_nom.get().strip()
        if nom == "":
            self.notifier("Nom invalide", "erreur")
            return None

        texte_note = self.entree_note.get().strip().replace(",", ".")
        try:
            age = int(self.entree_age.get())
            note = float(texte_note)
        except ValueError:
            self.notifier("Age : nombre entier. Note : nombre", "erreur")
            return None

        if not math.isfinite(note):
            self.notifier("Note invalide", "erreur")
            return None
        if age <= 0:
            self.notifier("Age invalide", "erreur")
            return None
        if note < 0 or note > 20:
            self.notifier("La note doit être entre 0 et 20", "erreur")
            return None

        note = round(note, 2)
        if note == int(note):
            note = int(note)

        return nom, age, note

    # ---------- Cartes d'étudiants ----------
    def creer_carte(self, parent, etudiant, selectable):
        carte = ctk.CTkFrame(parent, corner_radius=12, fg_color=CARTE_NORMALE)
        carte.pack(fill="x", padx=6, pady=4)

        pastille = ctk.CTkLabel(
            carte,
            text=etudiant.initiales(),
            width=44,
            height=44,
            corner_radius=22,
            fg_color=couleur_avatar(etudiant.nom),
            text_color="white",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        pastille.pack(side="left", padx=12, pady=10)

        infos = ctk.CTkFrame(carte, fg_color="transparent")
        infos.pack(side="left", pady=8)

        label_nom = ctk.CTkLabel(infos, text=etudiant.nom, font=ctk.CTkFont(size=16, weight="bold"))
        label_nom.pack(anchor="w")
        label_age = ctk.CTkLabel(infos, text=f"{etudiant.age} ans", text_color="gray")
        label_age.pack(anchor="w")

        if etudiant.est_admis():
            couleur_badge = "#27ae60"
            statut = "Admis"
        else:
            couleur_badge = "#c0392b"
            statut = "Ajourné"

        badge = ctk.CTkLabel(
            carte,
            text=f"{format_note(etudiant.note)}/20",
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
            if not (selectable and self.etudiant_selectionne is etudiant):
                carte.configure(fg_color=CARTE_SURVOL)

        def sortir(event=None):
            if selectable and self.etudiant_selectionne is etudiant:
                carte.configure(fg_color=CARTE_SELECTION)
            else:
                carte.configure(fg_color=CARTE_NORMALE)

        def cliquer(event=None):
            if selectable:
                self.selectionner(etudiant)

        widgets = [carte, pastille, infos, label_nom, label_age, badge, label_statut]
        for widget in widgets:
            widget.bind("<Enter>", entrer)
            widget.bind("<Leave>", sortir)
            widget.bind("<Button-1>", cliquer)

        return carte

    def colorer_cartes(self):
        for etudiant, carte in self.cartes_liste:
            if etudiant is self.etudiant_selectionne:
                carte.configure(fg_color=CARTE_SELECTION)
            else:
                carte.configure(fg_color=CARTE_NORMALE)

    def selectionner(self, etudiant):
        self.etudiant_selectionne = etudiant
        self.vider_champs()
        self.entree_nom.insert(0, etudiant.nom)
        self.entree_age.insert(0, str(etudiant.age))
        self.entree_note.insert(0, format_note(etudiant.note))
        self.colorer_cartes()

    # ---------- Tri et filtres ----------
    def changer_tri(self, valeur):
        self.filtres["tri"] = valeur
        self.rafraichir_liste()

    def changer_filtre(self, valeur):
        self.filtres["filtre"] = valeur
        self.rafraichir_liste()

    # ---------- Graphiques ----------
    def dessiner_graphiques(self, stats):
        if not MPL:
            return

        sombre = ctk.get_appearance_mode() == "Dark"
        fond = "#2b2b2b" if sombre else "#dbdbdb"
        texte = "white" if sombre else "black"

        self.figure.set_facecolor(fond)
        for axe in (self.axe_notes, self.axe_reussite):
            axe.clear()
            axe.axis("on")
            axe.set_facecolor(fond)

        if stats is None:
            compte = [0, 0, 0, 0]
            admis = 0
            ajournes = 0
        else:
            compte = stats["repartition"]
            admis = stats["admis"]
            ajournes = stats["ajournes"]

        self.axe_notes.bar(["0-5", "5-10", "10-15", "15-20"], compte,
                           color=["#e74c3c", "#e67e22", "#3498db", "#2ecc71"])
        self.axe_notes.set_title("Répartition des notes", color=texte, fontsize=11)
        self.axe_notes.tick_params(colors=texte)
        self.axe_notes.yaxis.set_major_locator(MaxNLocator(integer=True))
        for cote in ["top", "right"]:
            self.axe_notes.spines[cote].set_visible(False)
        for cote in ["left", "bottom"]:
            self.axe_notes.spines[cote].set_color(texte)

        self.axe_reussite.set_title("Admis / Ajournés", color=texte, fontsize=11)
        if stats is None:
            self.axe_reussite.text(0.5, 0.5, "Pas de données", ha="center", va="center",
                                   color=texte, transform=self.axe_reussite.transAxes)
            self.axe_reussite.axis("off")
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
            self.axe_reussite.pie(valeurs, labels=noms, colors=couleurs,
                                  autopct="%1.0f%%", textprops={"color": texte})

        self.figure.tight_layout()
        self.canvas_graphiques.draw()

    # ---------- Rafraîchissement ----------
    def vider_conteneur(self, conteneur):
        for widget in conteneur.winfo_children():
            widget.destroy()

    def rafraichir_liste(self):
        self.vider_conteneur(self.conteneur_liste)
        self.cartes_liste = []

        affiches = self.gestionnaire.obtenir(self.filtres["tri"], self.filtres["filtre"])
        if len(affiches) == 0:
            ctk.CTkLabel(self.conteneur_liste, text="Aucun étudiant à afficher.", text_color="gray").pack(pady=30)
            return

        for etudiant in affiches:
            carte = self.creer_carte(self.conteneur_liste, etudiant, True)
            self.cartes_liste.append((etudiant, carte))
        self.colorer_cartes()

    def rafraichir_recherche(self, event=None):
        self.vider_conteneur(self.conteneur_recherche)

        resultats = self.gestionnaire.obtenir("A-Z", "Tous", self.entree_recherche.get())
        for etudiant in resultats:
            self.creer_carte(self.conteneur_recherche, etudiant, False)

        self.label_resultats.configure(text=f"{len(resultats)} résultat(s)")

    def rafraichir_accueil(self):
        stats = self.gestionnaire.statistiques()

        if stats is None:
            self.cartes_stats["nombre"].configure(text="0")
            self.cartes_stats["moyenne"].configure(text="-")
            self.cartes_stats["admis"].configure(text="0")
            self.cartes_stats["ajournes"].configure(text="0")
            self.barre_taux.set(0)
            self.label_taux.configure(text="Taux de réussite : -")
            for label in self.podium_labels:
                label.configure(text="-")
            self.dessiner_graphiques(None)
            return

        self.cartes_stats["nombre"].configure(text=str(stats["nombre"]))
        self.cartes_stats["moyenne"].configure(text=f"{stats['moyenne']:.1f}".replace(".", ","))
        self.cartes_stats["admis"].configure(text=str(stats["admis"]))
        self.cartes_stats["ajournes"].configure(text=str(stats["ajournes"]))

        self.barre_taux.set(stats["taux"])
        self.label_taux.configure(text=f"Taux de réussite : {stats['taux'] * 100:.0f} %")

        medailles = ["🥇", "🥈", "🥉"]
        meilleurs = stats["meilleurs"]
        for i in range(3):
            if i < len(meilleurs):
                self.podium_labels[i].configure(
                    text=f"{medailles[i]}  {meilleurs[i].nom}  -  {format_note(meilleurs[i].note)}/20"
                )
            else:
                self.podium_labels[i].configure(text="-")

        self.dessiner_graphiques(stats)

    def rafraichir_tout(self):
        self.rafraichir_liste()
        self.rafraichir_recherche()
        self.rafraichir_accueil()

    # ---------- Actions ----------
    def ajouter(self):
        resultat = self.lire_champs()
        if resultat is None:
            return
        nom, age, note = resultat

        if self.gestionnaire.nom_existe(nom):
            if not self.confirmer("Doublon", f"Un étudiant nommé {nom} existe déjà. L'ajouter quand même ?"):
                return

        self.gestionnaire.ajouter(Etudiant(nom, age, note))
        self.etudiant_selectionne = None
        self.vider_champs()
        self.rafraichir_tout()
        self.notifier("Etudiant ajouté !")

    def modifier(self):
        etudiant = self.etudiant_selectionne
        if etudiant is None:
            self.notifier("Sélectionne un étudiant dans la liste", "attention")
            return

        resultat = self.lire_champs()
        if resultat is None:
            return
        nom, age, note = resultat

        if self.gestionnaire.nom_existe(nom, ignorer=etudiant):
            if not self.confirmer("Doublon", f"Un autre étudiant s'appelle déjà {nom}. Modifier quand même ?"):
                return

        self.gestionnaire.modifier(etudiant, nom, age, note)
        self.etudiant_selectionne = None
        self.vider_champs()
        self.rafraichir_tout()
        self.notifier("Etudiant modifié !")

    def supprimer(self):
        etudiant = self.etudiant_selectionne
        if etudiant is None:
            self.notifier("Sélectionne un étudiant dans la liste", "attention")
            return

        if not self.confirmer("Confirmation", f"Voulez-vous vraiment supprimer {etudiant.nom} ?"):
            return

        self.gestionnaire.supprimer(etudiant)
        self.etudiant_selectionne = None
        self.vider_champs()
        self.rafraichir_tout()
        self.notifier("Etudiant supprimé !", "erreur")

    def annuler(self):
        """Désélectionne l'étudiant et vide les champs."""
        self.etudiant_selectionne = None
        self.vider_champs()
        self.colorer_cartes()
        self.focus()

    def aller_ajouter(self):
        self.afficher_page("Étudiants")
        self.entree_nom.focus()


if __name__ == "__main__":
    app = Application()
    app.mainloop()