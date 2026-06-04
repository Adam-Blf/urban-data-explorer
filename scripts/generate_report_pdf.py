"""Genere le rapport de soutenance (.pdf) · Urban Data Explorer.

RNCP40875 · Bloc 1 · Expert en Ingenierie des Donnees.
Binome : Adam Beloucif & Emilien Morice.

Ton : rapport de SOUTENANCE (narratif, accessible), pas une doc technique.
Charte DSFR : bleu France #000091, rouge Marianne #E1000F, fond blanc.
Police de rendu : Helvetica (substitution systeme officielle de Marianne).
Regle de redaction : aucun tiret long ; on emploie '·', ':', ',' et '-'.

Dependance : fpdf2 (deja dans requirements.txt).
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]

# ── Palette DSFR (RGB) ────────────────────────────────────────────────────
BLUE = (0, 0, 145)
RED = (225, 0, 15)
INK = (22, 22, 22)
GREY = (58, 58, 58)
MENTION = (102, 102, 102)
LIGHT = (246, 246, 246)
BORDER = (221, 221, 221)
WHITE = (255, 255, 255)

# ── Co-branding EFREI (certificateur · Paris Pantheon-Assas) ──────────────
EFREI_AZURE = (20, 134, 201)   # bleu eFrei
EFREI_NAVY = (22, 55, 103)     # navy #163767
ASSETS = Path(__file__).resolve().parent / "assets"

AUTHORS = "Adam Beloucif & Emilien Morice"


class Report(FPDF):
    cover = False

    def header(self):
        if self.cover:
            return
        self.set_fill_color(*BLUE)
        self.rect(0, 0, 6, 297, "F")
        self.set_xy(15, 8)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*MENTION)
        self.cell(0, 5, "Urban Data Explorer  ·  Rapport de soutenance", align="L")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "RNCP40875 · Bloc 1", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*BORDER)
        self.set_line_width(0.3)
        self.line(15, 16, 195, 16)
        self.ln(12)

    def footer(self):
        if self.cover:
            return
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MENTION)
        self.cell(0, 5, AUTHORS, align="L")
        self.set_text_color(*BLUE)
        self.set_font("Helvetica", "B", 8)
        self.cell(0, 5, f"{self.page_no()}", align="R")

    # ── helpers ───────────────────────────────────────────────────────
    def h1(self, num, title):
        if self.get_y() > 250:
            self.add_page()
        self.ln(2)
        y = self.get_y()
        self.set_fill_color(*BLUE)
        self.rect(15, y, 8, 8, "F")
        self.set_xy(15, y)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*WHITE)
        self.cell(8, 8, str(num), align="C")
        self.set_xy(25, y)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*INK)
        self.cell(0, 8, " " + title, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def eyebrow(self, text):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*MENTION)
        self.cell(0, 5, text.upper(), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*GREY)
        self.multi_cell(0, 5.8, text)
        self.ln(2)

    def bullet(self, lead, rest=""):
        self.set_x(15)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*BLUE)
        self.write(5.8, chr(149) + "  ")
        self.set_text_color(*INK)
        self.write(5.8, lead)
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*GREY)
        self.write(5.8, rest)
        self.ln(8)

    def quote(self, text):
        """Encadre clair avec lisere bleu : pour une idee forte."""
        y = self.get_y()
        self.set_font("Helvetica", "I", 10.5)
        self.set_text_color(*GREY)
        # mesure approximative de hauteur
        self.set_fill_color(*LIGHT)
        h = 5.6 * (1 + len(text) // 95) + 6
        self.rect(15, y, 180, h, "F")
        self.set_fill_color(*BLUE)
        self.rect(15, y, 1.5, h, "F")
        self.set_xy(20, y + 3)
        self.multi_cell(170, 5.6, text)
        self.set_y(y + h + 3)

    def kpi_row(self, items):
        n = len(items)
        gap = 4
        w = (180 - gap * (n - 1)) / n
        x0, y0 = 15, self.get_y()
        for i, (val, lab) in enumerate(items):
            x = x0 + i * (w + gap)
            self.set_fill_color(*LIGHT)
            self.set_draw_color(*BORDER)
            self.rect(x, y0, w, 22, "DF")
            self.set_fill_color(*BLUE)
            self.rect(x, y0, 1.5, 22, "F")
            self.set_xy(x + 4, y0 + 3)
            self.set_font("Helvetica", "B", 19)
            self.set_text_color(*BLUE)
            self.cell(w - 6, 9, val)
            self.set_xy(x + 4, y0 + 13)
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*GREY)
            self.multi_cell(w - 6, 4, lab)
        self.set_y(y0 + 26)

    def table(self, headers, rows, col_w):
        self.set_font("Helvetica", "B", 9.5)
        self.set_fill_color(*BLUE)
        self.set_text_color(*WHITE)
        for h, w in zip(headers, col_w):
            self.cell(w, 8, " " + h, border=0, fill=True)
        self.ln(8)
        fill = False
        for row in rows:
            self.set_fill_color(*(LIGHT if fill else WHITE))
            for i, (cell, w) in enumerate(zip(row, col_w)):
                self.set_text_color(*(BLUE if i == 0 else GREY))
                self.set_font("Helvetica", "B" if i == 0 else "", 9)
                self.cell(w, 7, " " + cell, border=0, fill=True)
            self.ln(7)
            fill = not fill
        self.ln(2)


def main():
    pdf = Report()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 18, 15)
    pdf.alias_nb_pages()

    # ── Couverture ──────────────────────────────────────────────────────
    pdf.cover = True
    pdf.add_page()
    pdf.set_fill_color(*BLUE); pdf.rect(15, 25, 8, 24, "F")
    pdf.set_fill_color(*WHITE); pdf.set_draw_color(*BORDER); pdf.rect(23, 25, 8, 24, "DF")
    pdf.set_fill_color(*RED); pdf.rect(31, 25, 8, 24, "F")
    # logo EFREI (certificateur) en haut a droite
    efrei_logo = ASSETS / "efrei-logo.png"
    if efrei_logo.exists():
        pdf.image(str(efrei_logo), x=131, y=26, w=64)  # ratio 2:1 -> h=32
    pdf.set_xy(15, 52)
    pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*INK)
    pdf.cell(0, 6, "REPUBLIQUE FRANCAISE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10); pdf.set_text_color(*MENTION)
    pdf.cell(0, 5, "Donnees ouvertes · Ville de Paris", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(15, 95)
    pdf.set_font("Helvetica", "B", 34); pdf.set_text_color(*BLUE)
    pdf.cell(0, 16, "Urban Data Explorer", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 17); pdf.set_text_color(*GREY)
    pdf.cell(0, 10, "Observatoire socio-urbain de Paris", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_fill_color(*RED); pdf.rect(15, pdf.get_y(), 55, 1.5, "F"); pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(*INK)
    pdf.multi_cell(0, 7, "Rapport de soutenance")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11); pdf.set_text_color(*MENTION)
    pdf.cell(0, 6, "RNCP40875 · Bloc 1 · Expert en Ingenierie des Donnees", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Certificateur : Efrei · Paris Pantheon-Assas Universite", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Binome : {AUTHORS}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Soutenance 2026", new_x="LMARGIN", new_y="NEXT")
    # bandeau bas bicolore : bleu France (Etat) + azur EFREI (ecole)
    pdf.set_fill_color(*BLUE); pdf.rect(0, 282, 150, 15, "F")
    pdf.set_fill_color(*EFREI_AZURE); pdf.rect(150, 282, 60, 15, "F")
    pdf.cover = False

    # ── 1. Presentation ─────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(1, "Le projet en quelques mots")
    pdf.body(
        "Imaginez un decideur de la Ville de Paris qui veut comparer deux arrondissements : "
        "ou les loyers grimpent, ou il manque de logements sociaux, ou la qualite de vie est la "
        "meilleure. Aujourd'hui, ces reponses sont eparpillees dans des dizaines de jeux de donnees "
        "ouvertes, dans des formats differents. Notre projet rassemble ces donnees au meme endroit "
        "et les rend lisibles sur une carte interactive."
    )
    pdf.body(
        "Urban Data Explorer est un observatoire socio-urbain de Paris. On y explore, arrondissement "
        "par arrondissement, le marche immobilier, le logement social, les revenus, le cadre de vie et "
        "l'environnement. Derriere cette carte simple se cache une chaine de donnees complete, que nous "
        "presentons dans ce rapport : c'est elle qui valide les competences du Bloc 1."
    )
    pdf.quote(
        "Notre objectif : transformer des donnees publiques dispersees en un outil d'aide a la "
        "decision clair, fiable et agreable a utiliser."
    )
    pdf.kpi_row([("16", "sources Open Data"), ("8", "familles de donnees"),
                 ("20", "arrondissements"), ("5", "niveaux de zoom")])

    # ── 2. Demarche & binome ────────────────────────────────────────────
    pdf.h1(2, "Notre demarche et l'organisation du binome")
    pdf.body(
        "Le projet a ete mene en binome, en mode collectif. Nous avons travaille de maniere iterative : "
        "d'abord faire circuler la donnee de bout en bout (meme simplement), puis enrichir chaque maillon. "
        "Cette approche nous a permis d'avoir tres tot une demonstration qui fonctionne, puis de l'ameliorer."
    )
    pdf.bullet("Repartition : ", "un focus partage entre la chaine de donnees (ingestion, bases, API) et la "
               "restitution (carte, interface, experience utilisateur), avec des points de synchronisation reguliers.")
    pdf.bullet("Methode : ", "versionnage Git, decoupage en taches, et un mode local-first pour que chacun "
               "puisse faire tourner le projet sans dependre d'une infrastructure lourde.")
    pdf.bullet("Fil rouge : ", "rester guides par le besoin metier (comparer des arrondissements) plutot que "
               "par la technique pour la technique.")

    # ── 3. Architecture ─────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(3, "L'architecture en un coup d'oeil")
    pdf.body(
        "On peut resumer le projet comme le voyage d'une donnee, du fichier brut jusqu'a la carte. "
        "Ce voyage suit trois etapes (le pattern medaillon Bronze, Silver, Gold) :"
    )
    pdf.bullet("Bronze : ", "on recupere les fichiers Open Data tels quels et on les range proprement.")
    pdf.bullet("Silver : ", "on nettoie, on harmonise les codes d'arrondissement et on place chaque point sur la carte.")
    pdf.bullet("Gold : ", "on calcule les indicateurs prets a afficher et on les charge dans la base d'analyse.")
    pdf.body(
        "Ensuite, une API met ces donnees a disposition, et l'interface web les affiche sous forme de "
        "carte et de graphiques. En parallele, un flux temps reel alimente l'observatoire en evenements "
        "(disponibilite Velib, chantiers). Le tout peut tourner sur un simple poste, ou en mode distribue "
        "avec Docker."
    )
    pdf.eyebrow("Les briques techniques (langage clair)")
    pdf.bullet("Traitement : ", "Polars, un moteur de calcul tres rapide, pour transformer les donnees.")
    pdf.bullet("Bases de donnees : ", "PostgreSQL pour l'analyse structuree, Cassandra pour les flux d'evenements.")
    pdf.bullet("Lac de donnees : ", "des fichiers Parquet compresses, organises par etape.")
    pdf.bullet("API & interface : ", "FastAPI cote serveur, React et cartographie cote ecran (fond de plan IGN).")

    # ── 4. Donnees ──────────────────────────────────────────────────────
    pdf.h1(4, "Les donnees : richesse et qualite")
    pdf.body(
        "Nous integrons 16 sources Open Data de la Ville de Paris, regroupees en 8 familles : mobilite, "
        "education, logement, culture, sante, espaces verts, services publics et pression urbaine. Le defi "
        "principal a ete de relier chaque donnee a son arrondissement, meme quand l'information n'etait pas "
        "fournie."
    )
    pdf.bullet("Notre solution : ", "un geocodage qui fonctionne hors ligne, capable de retrouver l'arrondissement "
               "a partir des coordonnees geographiques, sans dependre d'un service externe.")
    pdf.bullet("Filet de securite : ", "si besoin, un appel a l'API nationale d'adresses prend le relais.")
    pdf.bullet("Tracabilite : ", "chaque donnee porte une etiquette de qualite indiquant comment elle a ete rattachee.")

    # ── 5. Ce que nous demontrons ───────────────────────────────────────
    pdf.add_page()
    pdf.h1(5, "Ce que nous demontrons (competences du Bloc 1)")
    pdf.body(
        "Le Bloc 1 evalue la capacite a construire une architecture de stockage et de traitement. Voici, "
        "en langage clair, ce que le projet met en oeuvre pour chaque competence."
    )
    pdf.eyebrow("Stocker la donnee")
    pdf.bullet("C1.1 · Base relationnelle : ", "un modele en etoile dans PostgreSQL, avec des regles d'integrite "
               "(cles, contraintes) et des index pour aller vite. Nous l'avons mis a l'epreuve par des tests de charge.")
    pdf.bullet("C1.2 · Base NoSQL : ", "Cassandra accueille les evenements en continu ; ils sont tries du plus recent "
               "au plus ancien et s'effacent automatiquement au bout de 7 jours.")
    pdf.bullet("C1.3 · Lac de donnees : ", "les fichiers Parquet organisent les donnees variees par etape, de maniere "
               "performante et econome.")
    pdf.bullet("C1.4 · Scalabilite : ", "grace a Docker, l'architecture peut grandir service par service ; le mode "
               "local-first garantit la continuite meme sans cluster.")
    pdf.ln(1)
    pdf.eyebrow("Traiter et exposer la donnee")
    pdf.bullet("C2.1 · API : ", "FastAPI rend les donnees accessibles et fournit une documentation interactive (/docs).")
    pdf.bullet("C2.2 · Streaming : ", "Kafka collecte les flux urbains en temps reel et les transmet a la base d'evenements.")
    pdf.bullet("C2.3 · Transformation : ", "Polars fusionne des sources heterogenes et les structure pour l'analyse.")
    pdf.bullet("C2.4 · Optimisation : ", "formats compresses et index garantissent un acces rapide, mesure par nos tests.")

    # ── 6. Demonstration interface ──────────────────────────────────────
    pdf.add_page()
    pdf.h1(6, "La demonstration : l'interface")
    pdf.body(
        "La partie visible du projet est un tableau de bord cartographique qui adopte les codes du Systeme "
        "de Design de l'Etat (DSFR) : police Marianne, bleu France, rouge Marianne et le bloc Republique "
        "Francaise. Un choix assume, qui inscrit l'outil dans une identite institutionnelle credible."
    )
    pdf.bullet("Carte officielle : ", "fond de plan IGN, avec un zoom progressif de la ville jusqu'au batiment.")
    pdf.bullet("Lecture immediate : ", "une coloration de la carte par indicateur, avec une legende dynamique.")
    pdf.bullet("Comparaison : ", "deux arrondissements affiches cote a cote pour trancher d'un coup d'oeil.")
    pdf.bullet("Soin de l'accessibilite : ", "contrastes conformes, theme clair et sombre, navigation au clavier.")
    # captures cote a cote : theme clair / theme sombre (ratio 1.6 -> h=55)
    light, dark = ROOT / "ude-light.png", ROOT / "ude-dark.png"
    y = pdf.get_y() + 3
    if light.exists():
        pdf.set_draw_color(*BORDER); pdf.rect(15, y, 88, 55)
        pdf.image(str(light), x=15, y=y, w=88)
    if dark.exists():
        pdf.set_draw_color(*BORDER); pdf.rect(107, y, 88, 55)
        pdf.image(str(dark), x=107, y=y, w=88)
    pdf.set_xy(15, y + 56)
    pdf.set_font("Helvetica", "I", 8.5); pdf.set_text_color(*MENTION)
    pdf.cell(88, 5, "Theme clair · fond de plan IGN", align="C")
    pdf.cell(4, 5, "")
    pdf.cell(88, 5, "Theme sombre · accessibilite WCAG AA", align="C")

    # Cote serveur : l'API documentee (Swagger)
    pdf.add_page()
    pdf.eyebrow("Cote serveur : l'API REST documentee")
    pdf.body(
        "Chaque jeu de donnees est expose par une API FastAPI qui se documente toute seule. Depuis le "
        "navigateur, on visualise et on teste en direct toutes les routes : etat du projet, catalogue des "
        "sources, indicateurs, contours geographiques et flux d'evenements."
    )
    banner = ASSETS / "ude-api-banner.png"
    if banner.exists():
        yb = pdf.get_y() + 1
        pdf.set_draw_color(*BORDER)
        pdf.rect(15, yb, 180, 124)
        pdf.image(str(banner), x=15, y=yb, w=180)
        pdf.set_y(yb + 126)
        pdf.set_font("Helvetica", "I", 8.5); pdf.set_text_color(*MENTION)
        pdf.cell(0, 5, "Documentation interactive /docs · routeurs health, catalog, datamarts, pipeline, events, repo",
                 align="C", new_x="LMARGIN", new_y="NEXT")

    # ── 7. Resultats ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(7, "Resultats et validation")
    pdf.body(
        "Pour prouver que la base relationnelle tient la charge, nous avons simule plusieurs utilisateurs "
        "lancant des requetes d'analyse en meme temps. Les resultats confirment la solidite du modele :"
    )
    pdf.table(
        ["Ce que nous avons mesure", "Resultat"],
        [["Requetes traitees sans erreur", "500 sur 500"],
         ["Vitesse de traitement", "environ 1 190 requetes par seconde"],
         ["Temps de reponse moyen", "1,80 ms"],
         ["Temps de reponse au pire des cas (p95)", "3,50 ms"],
         ["Regles d'integrite verifiees", "3 sur 3 validees"]],
        [120, 60],
    )
    pdf.body(
        "Autrement dit : meme sollicitee par plusieurs utilisateurs, la base repond en quelques "
        "millisecondes et n'accepte aucune donnee incoherente. C'est exactement ce qu'attend une "
        "gouvernance de donnees."
    )

    # ── 8. Bilan competences ────────────────────────────────────────────
    pdf.h1(8, "Bilan : couverture de la grille RNCP40875")
    pdf.table(
        ["Competence", "Comment le projet la valide"],
        [["C1.1", "Modele en etoile PostgreSQL + tests de charge reussis"],
         ["C1.2", "Cassandra pour les evenements (tri par date, purge 7 jours)"],
         ["C1.3", "Lac de donnees Bronze/Silver/Gold en Parquet"],
         ["C1.4", "Docker multi-services + mode local-first resilient"],
         ["C2.1", "API FastAPI documentee et accessible"],
         ["C2.2", "Streaming Kafka temps reel vers Cassandra"],
         ["C2.3", "Fusion et structuration des sources avec Polars"],
         ["C2.4", "Formats compresses et index pour un acces rapide"]],
        [30, 150],
    )

    # ── 9. Conclusion ───────────────────────────────────────────────────
    pdf.h1(9, "Conclusion et perspectives")
    pdf.body(
        "Urban Data Explorer demontre une chaine de donnees complete et coherente, du fichier brut "
        "jusqu'a la carte interactive, en couvrant l'ensemble des competences C1.1 a C2.4. Le projet "
        "est a la fois robuste (il tourne en local comme en distribue) et soigne (standards de l'Etat, "
        "accessibilite)."
    )
    pdf.bullet("Pour aller plus loin : ", "brancher les sources reelles de prix (DVF) et de revenus (INSEE), "
               "activer l'authentification de l'API, et envisager un deploiement dans le cloud avec des alertes "
               "sur les flux temps reel.")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 10.5)
    pdf.set_text_color(*MENTION)
    pdf.multi_cell(0, 5.8, "Merci de votre attention. Nous restons disponibles pour repondre a vos questions et "
                   "faire une demonstration en direct de l'outil.")

    out = ROOT / "rapport.pdf"
    pdf.output(str(out))
    print(f"Rapport genere: {out}  ({pdf.page_no()} pages)")


if __name__ == "__main__":
    main()
