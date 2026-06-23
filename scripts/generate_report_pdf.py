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

EFREI_AZURE = (20, 134, 201)
EFREI_NAVY = (22, 55, 103)
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
        self.cell(0, 5, "Urban Data Explorer  ·  Rapport de soutenance M1", align="L")
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

    def h2(self, title):
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*BLUE)
        self.set_fill_color(*LIGHT)
        self.rect(15, self.get_y(), 180, 7, "F")
        self.set_xy(17, self.get_y() + 0.5)
        self.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

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
        y = self.get_y()
        self.set_font("Helvetica", "I", 10.5)
        self.set_text_color(*GREY)
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
                self.cell(w, 7, " " + str(cell), border=0, fill=True)
            self.ln(7)
            fill = not fill
        self.ln(2)

    def family_card(self, name, label, count, items):
        y = self.get_y()
        self.set_fill_color(*LIGHT)
        self.set_draw_color(*BORDER)
        self.rect(15, y, 180, 8, "DF")
        self.set_fill_color(*BLUE)
        self.rect(15, y, 2, 8, "F")
        self.set_xy(20, y + 1)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*BLUE)
        self.cell(80, 6, label)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*INK)
        self.cell(0, 6, f"{count} sources", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        for item in items:
            self.set_x(22)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*GREY)
            self.cell(3, 5, chr(149))
            self.cell(0, 5, item, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)


def main():
    pdf = Report()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 18, 15)
    pdf.alias_nb_pages()

    # ── Couverture ──────────────────────────────────────────────────────────
    pdf.cover = True
    pdf.add_page()
    pdf.set_fill_color(*BLUE)
    pdf.rect(15, 25, 8, 24, "F")
    pdf.set_fill_color(*WHITE)
    pdf.set_draw_color(*BORDER)
    pdf.rect(23, 25, 8, 24, "DF")
    pdf.set_fill_color(*RED)
    pdf.rect(31, 25, 8, 24, "F")
    efrei_logo = ASSETS / "efrei-logo.png"
    if efrei_logo.exists():
        pdf.image(str(efrei_logo), x=131, y=26, w=64)
    pdf.set_xy(15, 52)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*INK)
    pdf.cell(0, 6, "REPUBLIQUE FRANCAISE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MENTION)
    pdf.cell(0, 5, "Donnees ouvertes · Ville de Paris · OpenStreetMap · data.gouv.fr", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(15, 90)
    pdf.set_font("Helvetica", "B", 34)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 16, "Urban Data Explorer", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 17)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 10, "Observatoire socio-urbain de Paris - Architecture medaillon", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_fill_color(*RED)
    pdf.rect(15, pdf.get_y(), 55, 1.5, "F")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*INK)
    pdf.multi_cell(0, 7, "Rapport de soutenance M1 - Data Engineering & IA")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*MENTION)
    pdf.cell(0, 6, "RNCP40875 · Bloc 1 · Expert en Ingenierie des Donnees", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Certificateur : Efrei · Paris Pantheon-Assas Universite", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Binome : {AUTHORS}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Annee 2025-2026", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*MENTION)
    pdf.cell(0, 5, "CONFIDENTIEL PEDA · ne pas diffuser hors jury", new_x="LMARGIN", new_y="NEXT")
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 282, 150, 15, "F")
    pdf.set_fill_color(*EFREI_AZURE)
    pdf.rect(150, 282, 60, 15, "F")
    pdf.cover = False

    # ── Sommaire ────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("", "Table des matieres")
    toc = [
        ("1", "Contexte et problematique"),
        ("2", "Organisation du binome et methode de travail"),
        ("3", "Architecture d'ensemble : le pattern medaillon"),
        ("4", "Stack technique"),
        ("5", "Le catalogue des sources : 83 jeux de donnees en 4 familles"),
        ("6", "Couverture OpenStreetMap : Overpass API"),
        ("7", "Pipeline ETL : de la source brute au datamart"),
        ("8", "Auto-ingestion hebdomadaire (Task Scheduler)"),
        ("9", "C1.1 · Base relationnelle PostgreSQL"),
        ("10", "C1.2 · Base NoSQL Cassandra"),
        ("11", "C1.3 / C1.4 · Data Lake Parquet et scalabilite"),
        ("12", "C2.1 · API REST FastAPI"),
        ("13", "C2.2 · Streaming Kafka temps reel"),
        ("14", "C2.3 / C2.4 · Transformation et optimisation"),
        ("15", "Indicateurs Gold et score de synthese"),
        ("16", "Qualite et tracabilite"),
        ("17", "Interface DSFR et accessibilite"),
        ("18", "Resultats et validation"),
        ("19", "Couverture de la grille RNCP40875"),
        ("20", "Conclusion et perspectives"),
    ]
    for num, title in toc:
        pdf.set_x(15)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*BLUE)
        pdf.cell(12, 6, num + ".")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GREY)
        pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # ── Resume executif ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("", "Resume executif")
    pdf.quote(
        "Urban Data Explorer est une plateforme d'ingenierie des donnees qui collecte, normalise et restitue "
        "83 jeux de donnees ouvertes sur Paris, en quatre familles thematiques, pour produire un observatoire "
        "socio-urbain comparatif par arrondissement."
    )
    pdf.kpi_row([("83", "sources integrees"), ("4", "familles"), ("20", "arrondissements"), ("118", "tests passes")])
    pdf.body(
        "Le projet met en oeuvre une architecture medaillon complete (Bronze, Silver, Gold), une API REST "
        "documentee, un streaming Kafka, une base relationnelle PostgreSQL et une base NoSQL Cassandra. "
        "Il couvre l'ensemble des competences C1.1 a C2.4 du Bloc 1 RNCP40875."
    )
    pdf.body(
        "Les donnees immobilieres (DVF 2023 · data.gouv.fr) et de revenus (INSEE Filosofi 2020) alimentent "
        "les indicateurs Gold avec des valeurs reelles. L'auto-ingestion hebdomadaire (Windows Task Scheduler, "
        "XML natif, sans .bat ni .ps1) garantit la fraicheur du catalogue chaque dimanche."
    )

    # ── 1. Contexte ─────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(1, "Contexte et problematique")
    pdf.body(
        "La Ville de Paris publie des centaines de jeux de donnees ouvertes sur opendata.paris.fr, "
        "data.gouv.fr et data.education.gouv.fr. Ces fichiers couvrent le logement social, la mobilite, "
        "la qualite de vie, l'environnement, les services publics, les commerces, et bien d'autres dimensions "
        "de la vie urbaine. Le probleme : ils sont disperses, dans des formats differents (CSV, TSV, GeoJSON), "
        "avec des references geographiques heterogenes (code postal, code INSEE, coordonnees GPS, code IRIS)."
    )
    pdf.body(
        "Un decideur - maire d'arrondissement, urbaniste, chercheur - qui veut comparer deux quartiers "
        "sur cinq indicateurs doit aujourd'hui assembler manuellement des dizaines de fichiers. "
        "Ce projet repond a ce besoin en construisant une chaine de donnees qui fait ce travail "
        "automatiquement et produit un observatoire cartographique pret a l'emploi."
    )
    pdf.h2("La question centrale")
    pdf.body(
        "Comment concevoir une architecture de donnees robuste, evolutive et pertinente pour produire "
        "un observatoire socio-urbain de Paris a partir de sources heterogenes publiques, en couvrant "
        "l'ensemble des competences d'architecture de stockage et de traitement du Bloc 1 RNCP40875 ?"
    )
    pdf.h2("Perimetre")
    pdf.bullet("Geographique : ", "Paris intra-muros, 20 arrondissements, 80 quartiers IRIS.")
    pdf.bullet("Thematique : ", "mobilite, vie quotidienne (education, sante, commerce, culture), environnement, logement et urbanisme.")
    pdf.bullet("Temporel : ", "donnees millésimees 2020-2024 ; flux temps reel Velib' et chantiers.")
    pdf.bullet("Technique : ", "ingestion, stockage multi-modele, traitement Polars, API REST, streaming Kafka, interface cartographique.")

    # ── 2. Binome ───────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(2, "Organisation du binome et methode de travail")
    pdf.body(
        "Le projet a ete conduit en binome (Adam Beloucif & Emilien Morice) sur toute la duree du semestre. "
        "La methode choisie est iterative : d'abord faire circuler la donnee de bout en bout avec un catalogue "
        "minimal, puis etendre le catalogue, enrichir les transformations et soigner l'interface."
    )
    pdf.h2("Repartition des roles")
    pdf.bullet("Ingestion & ETL : ", "conception du catalogue SourceSpec, pipeline Bronze/Silver/Gold, geocodage hors ligne, auto-ingestion Task Scheduler.")
    pdf.bullet("Base de donnees : ", "schema en etoile PostgreSQL, modelisation Cassandra, tests de charge.")
    pdf.bullet("API & streaming : ", "routeurs FastAPI, auth JWT, quotas par IP, producteur/consommateur Kafka.")
    pdf.bullet("Interface : ", "dashboard React/TypeScript, carte MapLibre (fond IGN), theme DSFR clair/sombre.")
    pdf.h2("Methode agile simplifiee")
    pdf.body(
        "Chaque iteration commence par une revue du catalogue (quelles sources manquent, quels indicateurs "
        "sont faux) et se termine par un commit granulaire et un test de fumee de l'API. Le versionnage Git "
        "avec branche feat/* + pull request assure la tracabilite de chaque decision."
    )
    pdf.h2("Environnements")
    pdf.bullet("Local-first : ", "le projet tourne sur un simple poste sans Docker ni base externe, grace aux fallbacks Parquet et aux constantes de reference.")
    pdf.bullet("Distribue : ", "Docker Compose avec 11 services (api, postgres, cassandra, kafka, zookeeper, hadoop, hive, spark, frontend, nginx, prometheus).")
    pdf.bullet("CI : ", "118 tests pytest passes a chaque push ; pas de secrets commites (.env gitignored).")

    # ── 3. Architecture ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(3, "Architecture d'ensemble : le pattern medaillon")
    pdf.body(
        "Le projet suit l'architecture medaillon, un pattern de reference en ingenierie des donnees qui "
        "organise les donnees en trois couches successives. Chaque couche correspond a un niveau de maturite "
        "de la donnee."
    )
    pdf.h2("Bronze · la donnee brute")
    pdf.body(
        "Les fichiers sont telecharges tels quels depuis les sources officielles et stockes dans "
        "data/raw/downloads/. Un fichier Bronze est une photographie exacte de la source a un instant t. "
        "Il n'est jamais modifie apres ingestion. Format : CSV, TSV (Overpass), ou CSV.GZ (gros jeux data.gouv.fr)."
    )
    pdf.h2("Silver · la donnee normalisee")
    pdf.body(
        "Le pipeline ETL (Polars) transforme chaque fichier Bronze en un enregistrement normalise "
        "appelable un 'record Silver'. Chaque record contient : source_id, family, arrondissement_code "
        "(normalise 75001-75020), latitude, longitude, code_iris, nom_iris, address, quality_flag. "
        "Le geocodage est realise hors ligne par point-in-polygon sur les contours IRIS (GeoJSON officiel IGN), "
        "sans aucun appel reseau externe lors du traitement."
    )
    pdf.h2("Gold · le datamart")
    pdf.body(
        "A partir du Silver, on construit deux datamarts : le dashboard (une ligne par arrondissement, "
        "avec tous les indices calcules) et la timeline (20 arrondissements x 12 mois = 240 lignes). "
        "Ces datamarts sont stockes en Parquet (local-first) et charges dans PostgreSQL (mode distribue). "
        "Ils alimentent directement l'API et l'interface cartographique."
    )
    pdf.h2("Schema de flux")
    pdf.quote(
        "Source Open Data  ->  Bronze (CSV/TSV raw)  ->  Silver (Polars, geocodage IRIS, normalisation)  "
        "->  Gold (datamarts Parquet / PostgreSQL)  ->  API FastAPI  ->  Interface React/MapLibre"
    )
    pdf.body(
        "En parallele, un flux temps reel (Kafka) collecte les evenements de disponibilite Velib' et "
        "de chantiers perturbants, les achemine dans Cassandra, et les expose via le routeur /events de l'API."
    )

    # ── 4. Stack ────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(4, "Stack technique")
    pdf.table(
        ["Couche", "Technologie", "Role"],
        [
            ["Traitement", "Python 3.12 + Polars", "ETL vectorise (moteur Rust), transformations Silver/Gold"],
            ["Base relationnelle", "PostgreSQL 15", "Datamart dashboard en schema etoile, tests de charge"],
            ["Base NoSQL", "Cassandra 4", "Stockage evenements temps reel, TTL 7 jours, partitionnement"],
            ["Data Lake", "Parquet + HDFS", "Couches Bronze/Silver/Gold, columnar, compresse (Snappy)"],
            ["Streaming", "Apache Kafka + Zookeeper", "Pipeline temps reel : Velib, chantiers; producteur/consommateur"],
            ["API", "FastAPI + Pydantic v2", "REST, auth JWT HS256, quotas par IP, documentation /docs"],
            ["Interface", "React + TypeScript + MapLibre", "Carte 2D (tuiles IGN Geoplateforme), chartjs, theme DSFR"],
            ["CI/CD", "pytest (118 tests)", "Couverture complete ETL, API, securite, qualite"],
            ["Orchestration", "Docker Compose 11 services", "Mode distribue optionnel, profils streaming & lake"],
            ["Ingestion auto", "Windows Task Scheduler (XML)", "Ingestion hebdomadaire, sans .bat ni .ps1 (EDR hospitaliers)"],
        ],
        [38, 50, 92],
    )
    pdf.body(
        "Le choix de Polars (moteur Rust) plutot que pandas s'explique par les performances : Polars "
        "est entre 5 et 10 fois plus rapide sur les transformations de type groupby/agg, ce qui est "
        "determinant quand on traite 83 sources en une passe hebdomadaire. La memoire est egalement "
        "mieux geree grace au lazy evaluation plan."
    )

    # ── 5. Catalogue ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(5, "Le catalogue des sources : 83 jeux de donnees en 4 familles")
    pdf.body(
        "L'ingenierie du catalogue est au coeur du projet. Chaque source est definie par un objet "
        "SourceSpec (dataclass Python immutable) qui encapsule l'identifiant, le titre, la famille, "
        "l'URL de telechargement, le fournisseur, le separateur, l'encodage, et les hints de geocodage "
        "(colonnes latitude/longitude, geo_point, arrondissement, adresse)."
    )
    pdf.quote(
        "83 sources · 4 familles · 3 fournisseurs principaux (opendata.paris.fr, data.gouv.fr, "
        "OpenStreetMap Overpass) · 30 sources OSM (Overpass API)"
    )

    pdf.family_card("mobilite", "Mobilite & Accessibilite", 17, [
        "Velib stations + disponibilite temps reel",
        "Amenagements cyclables (pistes, bandes)",
        "Stationnement voie publique (points et emprises)",
        "Bornes recharge electrique IRVE (Belib)",
        "Points d'arret IDFM (Ile-de-France Mobilites)",
        "Comptages velos permanents, WiFi gratuit Paris",
        "Chantiers perturbants, voirie parisienne",
        "OSM : bus, metro, tramway, velos en libre-service, taxi, parking",
    ])

    pdf.family_card("vie_quotidienne", "Vie quotidienne", 42, [
        "Education : ecoles mat./elem., colleges, lycees (annuaire MENJ), creches, bibliotheques",
        "Sante : defibrillateurs, sanisettes, hopitaux IDF, medecins HAS, pharmacies (OSM)",
        "Commerce : marches, Semaest, fontaines a boire, kiosques, equipements sportifs",
        "Culture : agenda Que Faire a Paris, lieux de tournage, musees de France, lieux de culte (OSM)",
        "OSM : restaurants, cafes, epiceries, boulangeries, banques, hotels, coiffeurs, librairies",
        "OSM : creches (OSM), gymnases, pompiers, dentistes, medecins generalistes",
    ])

    pdf.family_card("environnement", "Environnement & Cadre de vie", 12, [
        "Espaces verts (parcs, squares, promenades)",
        "Jardins partages, ilots de fraicheur, aire de jeux",
        "Ilots de chaleur (vulnerabilite thermique IRIS)",
        "Arbres de Paris (280 000 + alignement et parcs)",
        "Bruit - indicateurs Lden 2022",
        "OSM : arcs cyclables supplementaires, jardins communautaires",
    ])

    pdf.family_card("logement_urbanisme", "Logement & Urbanisme", 12, [
        "Logements sociaux finances (inventaire par arr.)",
        "DPE - Diagnostics de Performance Energetique (ADEME)",
        "Logements vacants taxables LOVAC (DGALN)",
        "Permis de construire deposes a Paris",
        "Monuments Historiques (referentiel national)",
        "DVF - Transactions immobilieres 2023 (DGFiP)",
        "INSEE Filosofi - Revenus par IRIS 2020",
        "Amiante/SIS (BRGM Georisques), ascenseurs, accessibilite PMR",
    ])

    pdf.body(
        "La conception du catalogue respecte le principe open data pur : uniquement des sources officielles "
        "publiques (Ville de Paris, Etat, OpenStreetMap). Aucun scraping de site prive ou sous paywall. "
        "Les 30 sources OSM sont interrogees via l'Overpass API avec un filtre de zone precise "
        "(area[\"ref:INSEE\"=\"75056\"]) pour limiter le perimetre exactement a la commune de Paris."
    )

    # ── 6. OSM ──────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(6, "Couverture OpenStreetMap : Overpass API")
    pdf.body(
        "OpenStreetMap (OSM) est la base cartographique collaborative la plus complete au monde. "
        "Elle documente des points d'interet que les jeux de donnees officiels ne couvrent pas ou "
        "couvrent mal : restaurants, pharmacies, lieux de culte, transports de surface, commerces de "
        "proximite, bornes de service. Le projet interroge OSM via l'Overpass API, un service de "
        "requetage en lecture sur la base OSM."
    )
    pdf.h2("Protocole technique")
    pdf.body(
        "Chaque source OSM est definie par une requete Overpass QL stockee dans le champ download_url "
        "avec le prefixe 'OVERPASS:'. L'auto-ingestion detecte ce prefixe et envoie la requete en POST "
        "(les requetes Overpass peuvent depasser 2 000 caracteres). Le format de sortie est TSV "
        "(tabulation-separated) avec en-tete, ce qui simplifie l'import Polars."
    )
    pdf.quote(
        "Exemple de requete Overpass QL pour les pharmacies : "
        "[out:csv(::lat,::lon,name,amenity,opening_hours,phone;true;'\\t')][timeout:90];"
        "area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=pharmacy](area.p);out body;"
    )
    pdf.body(
        "Le filtre area[\"ref:INSEE\"=\"75056\"] est plus fiable que area[name=\"Paris\"] car il "
        "cible le code INSEE exact de la commune de Paris (75056) plutot que le nom, qui peut correspondre "
        "a plusieurs communes en France."
    )
    pdf.h2("Sources OSM integrees (extrait)")
    pdf.table(
        ["Famille", "Source OSM", "Filtre amenity/shop"],
        [
            ["mobilite", "Arrets de bus", "highway=bus_stop"],
            ["mobilite", "Stations de metro", "station=subway"],
            ["mobilite", "Parkings auto", "amenity=parking"],
            ["vie_quotidienne", "Pharmacies", "amenity=pharmacy"],
            ["vie_quotidienne", "Restaurants", "amenity=restaurant"],
            ["vie_quotidienne", "Lieux de culte", "amenity=place_of_worship"],
            ["vie_quotidienne", "Epiceries", "shop=convenience"],
            ["vie_quotidienne", "Boulangeries", "shop=bakery"],
            ["vie_quotidienne", "Banques / DAB", "amenity=bank"],
            ["environnement", "Jardins comm.", "leisure=garden"],
        ],
        [42, 60, 78],
    )

    # ── 7. Pipeline ETL ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(7, "Pipeline ETL : de la source brute au datamart")
    pdf.h2("Etape 1 · Ingestion Bronze")
    pdf.body(
        "Le script auto_ingest.py parcourt le catalogue ALL_SOURCES et telecharge chaque source. "
        "Deux modes : HTTP GET (avec retry exponentiel, 3 tentatives) pour les API Opendatasoft et "
        "data.gouv.fr ; POST Overpass pour les sources OSM. Un rate-limiting de 0,5 s entre chaque "
        "source evite de surcharger les API publiques. Chaque fichier est nomme {source_id}.csv "
        "ou {source_id}.tsv dans data/raw/downloads/."
    )
    pdf.h2("Etape 2 · Transformation Silver")
    pdf.body(
        "La fonction build_silver_record(row, spec) transforme chaque ligne CSV en un record Silver. "
        "Elle applique dans l'ordre : (1) extraction des coordonnees GPS (colonnes latitude/longitude "
        "ou geo_point 'lat,lon'), (2) geocodage IRIS par point-in-polygon (polygones IRIS charges en "
        "memoire depuis le GeoJSON officiel), (3) normalisation du code arrondissement (75101 -> 75001, "
        "750 -> 75001 etc.), (4) attribution du quality_flag selon la precision du rattachement."
    )
    pdf.bullet("quality_flag = 'gps_iris' : ", "rattachement par point-in-polygon sur les contours IRIS.")
    pdf.bullet("quality_flag = 'code_only' : ", "code arrondissement fourni directement par la source, sans GPS.")
    pdf.bullet("quality_flag = 'unresolved' : ", "ni GPS ni code arrondissement exploitable.")
    pdf.h2("Etape 3 · Agregation Gold")
    pdf.body(
        "La fonction build_gold_dashboard(silver_df) agregee les records Silver par arrondissement et "
        "par famille. Elle calcule les 4 comptes de famille (environnement_count, mobilite_count, "
        "vie_quotidienne_count, logement_urbanisme_count), puis les indices derives "
        "(immobilier, logement social, revenu, cadre de vie, environnement) et le score global."
    )
    pdf.body(
        "Les valeurs de prix au m2 et de revenu median sont chargees depuis les sources reelles "
        "(DVF 2023 et INSEE Filosofi 2020) si les fichiers sont disponibles ; sinon, les constantes "
        "de reference (valeurs mesurees sur les donnees 2023) servent de fallback transparent."
    )
    pdf.h2("Tests de l'ETL")
    pdf.body(
        "118 tests pytest couvrent l'ensemble du pipeline : _family_counts, build_gold_dashboard "
        "(shape, valeurs dans plage, source reel vs reference), build_silver_record (geocodage, "
        "normalisation), _enrich_district_row (preservation des valeurs reelles, fallback), "
        "et les endpoints API (catalog, health, datamarts, auth, quotas)."
    )

    # ── 8. Auto-ingestion ───────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(8, "Auto-ingestion hebdomadaire")
    pdf.body(
        "Pour maintenir le catalogue a jour sans intervention manuelle, un Task Scheduler Windows "
        "declenche l'ingestion chaque dimanche a 04h00. La planification est definie dans un fichier XML "
        "(tasks/urban_ingest_sunday.xml) importe via la commande schtasks."
    )
    pdf.quote(
        "schtasks /Create /XML tasks\\urban_ingest_sunday.xml /TN \"AdamBrain\\UrbanDataIngestSunday\""
    )
    pdf.h2("Contrainte EDR hospitaliere")
    pdf.body(
        "Le projet est developpe dans un environnement ou Microsoft Defender for Endpoint (MDE) est "
        "deploye. Les scripts .bat et .ps1 sont bloques par l'EDR. La solution : action directe "
        "python.exe + chemin du script dans le XML Task Scheduler, sans aucune couche PowerShell. "
        "Cette contrainte est documentee et respectee dans tout le projet."
    )
    pdf.h2("Parametres de la tache")
    pdf.table(
        ["Parametre", "Valeur"],
        [
            ["Declencheur", "Chaque dimanche a 04h00"],
            ["Commande", "C:\\...\\Python312\\python.exe"],
            ["Arguments", "C:\\...\\urban-data-explorer\\scripts\\auto_ingest.py"],
            ["Duree max", "2 heures (PT2H)"],
            ["Sur batterie", "Oui (DisallowStartIfOnBatteries=false)"],
            ["Instances multiples", "IgnoreNew"],
        ],
        [60, 120],
    )
    pdf.body(
        "En mode --dry-run, le script simule l'ingestion sans ecrire de fichier, ce qui permet de "
        "valider la configuration du catalogue. En mode normal, il telecharge toutes les sources "
        "non metadata_only et journalise le resultat (ok/fail par source)."
    )

    # ── 9. C1.1 PostgreSQL ──────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(9, "C1.1 · Base relationnelle PostgreSQL")
    pdf.body(
        "PostgreSQL 15 est le moteur relationnel du projet. Il stocke les datamarts Gold sous la forme "
        "d'un schema en etoile concu pour l'analyse par arrondissement. Ce choix correspond a la "
        "competence C1.1 : 'Concevoir et implementer une base de donnees relationnelle scalable'."
    )
    pdf.h2("Schema en etoile")
    pdf.bullet("fact_arrondissement_dashboard : ", "table de faits (une ligne par arrondissement) avec tous les indices calcules, prix_m2, revenu_median, score global.")
    pdf.bullet("dim_arrondissement : ", "dimension geographique (code INSEE, nom, label, coordonnees centroide).")
    pdf.bullet("dim_iris : ", "dimension quartier IRIS (code, nom, code_com).")
    pdf.bullet("dim_source : ", "dimension source (source_id, titre, famille, fournisseur).")
    pdf.h2("Regles d'integrite")
    pdf.body(
        "Le schema impose des cles primaires, des cles etrangeres vers les dimensions, des contraintes "
        "NOT NULL sur les colonnes critiques et des contraintes CHECK sur les plages d'indices "
        "(0-100). Ces regles ont ete verifiees par les tests d'integrite referentielle du benchmark."
    )
    pdf.h2("Tests de charge")
    pdf.table(
        ["Ce que nous avons mesure", "Resultat"],
        [
            ["Requetes traitees sans erreur", "500 sur 500"],
            ["Debit moyen", "environ 1 190 requetes par seconde"],
            ["Temps de reponse moyen", "1,80 ms"],
            ["Temps de reponse p95", "3,50 ms"],
            ["Integrite referentielle verifiee", "3 sur 3 contraintes PASSED"],
        ],
        [120, 60],
    )
    pdf.body(
        "Le benchmark a ete realise avec 10 threads concurrents sur 500 requetes analytiques (GROUP BY, "
        "ORDER BY score DESC, filtres sur les indices). Les index sur les cles etrangeres et sur le "
        "score global sont determinants pour maintenir la latence p95 sous 4 ms."
    )

    # ── 10. C1.2 Cassandra ──────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(10, "C1.2 · Base NoSQL Cassandra")
    pdf.body(
        "Apache Cassandra est utilise pour stocker les evenements du flux temps reel : "
        "disponibilite des stations Velib' et evenements de chantiers. Le choix de Cassandra "
        "est justifie par ses caracteristiques : ecritures massives en O(1), modele append-only "
        "adapte aux flux d'evenements, et TTL natif pour la purge automatique."
    )
    pdf.h2("Modelisation orientee requetes")
    pdf.body(
        "La table events_by_type est partitionnee par event_type (velib_update, chantier_update, "
        "etc.) et triee par event_time DESC dans le clustering. Cette conception garantit que la "
        "requete 'donner les N evenements recents d'un type donne' est O(N) sans scan complet."
    )
    pdf.quote("PRIMARY KEY (event_type, event_time DESC, event_id) · TTL 604 800 s (7 jours) · RF=1 SimpleStrategy")
    pdf.h2("Complementarite SQL/NoSQL")
    pdf.body(
        "PostgreSQL et Cassandra coexistent et se complementent. PostgreSQL sert l'analytique structuree "
        "(comparaison d'arrondissements, calcul de scores, jointures) ; Cassandra sert le flux "
        "d'evenements (derniers snapshots Velib, alertes chantiers). L'API expose les deux "
        "via des routeurs distincts (/datamarts et /events)."
    )

    # ── 11. C1.3 / C1.4 ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(11, "C1.3 / C1.4 · Data Lake Parquet et scalabilite")
    pdf.h2("C1.3 · Data Lake")
    pdf.body(
        "Les donnees sont stockees en Parquet, un format colonnaire compresse (codec Snappy) "
        "particulierement adapte aux requetes analytiques. Chaque couche (Bronze, Silver, Gold) "
        "est un repertoire de fichiers Parquet partitionnes. En mode distribue, ces fichiers "
        "sont sur HDFS (Hadoop Distributed File System) ; en mode local-first, dans le systeme "
        "de fichiers local. Le code ne change pas entre les deux modes."
    )
    pdf.body(
        "L'integration de sources variees (CSV tabulaire, TSV Overpass, CSV.GZ data.gouv.fr) "
        "est prise en charge par le catalogue via les attributs separator et encoding de SourceSpec. "
        "Polars adapte automatiquement la lecture au format declare."
    )
    pdf.h2("C1.4 · Scalabilite et resilience")
    pdf.bullet("Docker Compose : ", "11 services (api, postgres, cassandra, kafka, zookeeper, hadoop, hive, spark, frontend, nginx, prometheus), profils activables (streaming, lake).")
    pdf.bullet("Healthchecks : ", "sondes de sante sur postgres, cassandra et l'API ; l'api attend que les bases soient prets avant de demarrer.")
    pdf.bullet("Volumes persistants : ", "les donnees postgres et cassandra survivent aux redemarrages de conteneurs.")
    pdf.bullet("Mode local-first : ", "si PostgreSQL n'est pas disponible, l'API retombe sur les Parquet locaux et les constantes de reference ; la carte reste fonctionnelle.")
    pdf.bullet("Haute disponibilite : ", "Kafka + Zookeeper pour la tolerance aux pannes du streaming ; Hadoop namenode/datanode pour le Data Lake distribue.")

    # ── 12. C2.1 API ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(12, "C2.1 · API REST FastAPI")
    pdf.body(
        "L'API est implementee avec FastAPI (ASGI, Pydantic v2) et se documente automatiquement "
        "via Swagger a l'adresse /docs et ReDoc a /redoc. Elle est le point d'acces unique entre "
        "le backend de donnees et l'interface cartographique."
    )
    pdf.h2("Routeurs metier")
    pdf.table(
        ["Routeur", "Prefix", "Role"],
        [
            ["health", "/health", "Sonde de vie, version, statut des bases"],
            ["auth", "/auth", "Login JWT, refresh token, revocation"],
            ["catalog", "/catalog", "Liste des 83 sources, famille, provider"],
            ["datamarts", "/datamarts", "Dashboard Gold, timeline 12 mois, comparaison"],
            ["pipeline", "/pipeline", "Declenchement ETL, statut, logs"],
            ["events", "/events", "Flux Cassandra (Velib, chantiers)"],
            ["repo", "/repo", "Metadonnees projet (version, stats)"],
            ["search", "/search", "Recherche full-text sur les sources"],
        ],
        [30, 35, 115],
    )
    pdf.h2("Securite")
    pdf.bullet("Auth JWT HS256 : ", "access token 60 min, refresh token 7 jours. Roles : viewer (lecture) et admin (pipeline, admin).")
    pdf.bullet("Quotas par IP : ", "anonyme 120 req/min, authentifie 600 req/min. Reponse HTTP 429 si depassement.")
    pdf.bullet("CORS restreint : ", "liste blanche via la variable UDE_CORS_ORIGINS (origine du frontend).")
    pdf.bullet("Stack traces : ", "jamais exposes cote client ; uniquement dans les logs serveur.")

    # ── 13. C2.2 Streaming ──────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(13, "C2.2 · Streaming Kafka temps reel")
    pdf.body(
        "Apache Kafka est le bus de messages du projet. Il decouple les producteurs de donnees "
        "en temps reel (Velib disponibilite, chantiers perturbants) des consommateurs "
        "(ecriture dans Cassandra, restitution dans l'interface)."
    )
    pdf.h2("Producteur")
    pdf.body(
        "Le producteur (streaming/velib_producer.py) interroge l'API temps reel de Velib' "
        "et publie un evenement JSON par station mise a jour sur le topic velib_updates. "
        "Un producteur similaire couvre les chantiers perturbants la circulation."
    )
    pdf.h2("Consommateur")
    pdf.body(
        "Le consommateur (streaming/consumer.py) lit les topics et ecrit les evenements dans "
        "Cassandra avec un TTL de 7 jours. L'API route /events interroge Cassandra pour "
        "servir les N derniers evenements d'un type donne."
    )
    pdf.h2("Infrastructure")
    pdf.body(
        "Kafka + Zookeeper sont orchestres via le profil 'streaming' de Docker Compose. "
        "En mode local (sans Docker), le streaming est desactive mais l'API reste disponible "
        "sur les donnees statiques."
    )

    # ── 14. C2.3 / C2.4 ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(14, "C2.3 / C2.4 · Transformation et optimisation")
    pdf.h2("C2.3 · Integration et transformation")
    pdf.body(
        "Polars est le moteur de transformation. Il lit les fichiers CSV/TSV en streaming "
        "(scan_csv/scan_ipc), applique les transformations paresseuses (lazy frame), et "
        "materialise uniquement le resultat final. Les principales transformations :"
    )
    pdf.bullet("Normalisation codes : ", "75101 -> 75001, codes a 3 chiffres (750) -> 75001, codes sur 2 chiffres (01) -> 75001.")
    pdf.bullet("Parsing geo_point : ", "chaine '48.85, 2.35' -> (lat=48.85, lon=2.35).")
    pdf.bullet("Geocodage IRIS : ", "algorithme ray-casting sur les polygones IRIS charges en memoire (GeoJSON IGN).")
    pdf.bullet("Fusion multi-sources : ", "sources DVF (CSV.GZ 250 Mo) + INSEE Filosofi (parquet) integrees dans build_gold_dashboard.")
    pdf.h2("C2.4 · Optimisation")
    pdf.body(
        "Plusieurs strategies d'optimisation sont appliquees pour garantir des temps de reponse "
        "sub-millisecondes et une empreinte memoire raisonnable :"
    )
    pdf.bullet("Parquet colonnaire : ", "les colonnes inutiles ne sont pas lues (projection pushdown). Compression Snappy reduit les fichiers de 60-70%.")
    pdf.bullet("Index PostgreSQL : ", "sur arrondissement_code (FK), score DESC, famille. Latence p95 < 4 ms sous charge.")
    pdf.bullet("lru_cache : ", "source_catalog() et source_family_counts() sont mis en cache en memoire apres le premier appel.")
    pdf.bullet("Polars lazy : ", "plan d'execution optimise avant materialisation, filtrages et agregations pousses au plus pres des sources.")
    pdf.bullet("quality_flag : ", "drapeau de qualite permettant de filtrer les enregistrements non rattaches avant l'agregation Gold.")

    # ── 15. Indicateurs Gold ────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(15, "Indicateurs Gold et score de synthese")
    pdf.body(
        "Le datamart Gold produit six indicateurs principaux par arrondissement, sur une echelle 0-100, "
        "plus un score global (moyenne des cinq indices). Ces indicateurs sont au coeur de la restitution "
        "cartographique et de la comparaison entre arrondissements."
    )
    pdf.table(
        ["Indicateur", "Source", "Formule (simplifiee)"],
        [
            ["immobilier_idx", "DVF 2023 (reel) ou reference", "(prix_m2 - 8000) / (16000 - 8000) * 100, clampe 10-95"],
            ["logement_social_idx", "Inventaire logements sociaux Paris", "pct_logements_sociaux * 2.5, clampe 5-95"],
            ["revenu_idx", "INSEE Filosofi 2020 (reel) ou ref.", "(revenu_median - 20000) / (48000 - 20000) * 100, clampe 10-95"],
            ["cadre_vie_idx", "Silver (accessibilite calculee)", "34 + env*2.5 + mob*0.8 + vq*1.5, clampe 12-96"],
            ["environnement_idx", "Silver (count environnement)", "env_count * 7.5, clampe 20-95"],
            ["score", "Agregation", "Moyenne(5 indices), arrondi"],
        ],
        [38, 48, 94],
    )
    pdf.body(
        "L'indicateur KPI specifique demande par l'enonce est l'accessibilite au logement, "
        "exprime en m2 achetables avec un an de revenu median : m2_abordables = revenu_median / prix_m2. "
        "Cet indicateur est traduit en indice (accessibilite_idx) sur 0-100 (4 m2/an = 100)."
    )
    pdf.h2("Tracabilite des sources de valeur")
    pdf.body(
        "Chaque arrondissement porte un champ data_source : 'real' si les valeurs DVF/Filosofi "
        "proviennent des fichiers telechargees, 'reference' si les constantes de reference "
        "sont utilisees en fallback. Ce drapeau est visible dans l'API et dans l'interface."
    )

    # ── 16. Qualite ─────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(16, "Qualite et tracabilite")
    pdf.body(
        "La qualite est une preoccupation transversale du projet. Chaque enregistrement Silver "
        "porte un quality_flag qui documente comment le rattachement geographique a ete obtenu. "
        "Cela permet de filtrer les enregistrements de faible qualite avant l'agregation Gold "
        "et de monitorer la proportion de donnees bien geocodees."
    )
    pdf.h2("Niveaux de qualite")
    pdf.table(
        ["quality_flag", "Signification", "Precision"],
        [
            ["gps_iris", "Rattachement par GPS (point-in-polygon IRIS)", "Haute"],
            ["gps_arr", "Rattachement par GPS (contours arrondissement)", "Bonne"],
            ["code_only", "Code arrondissement fourni par la source", "Moyenne"],
            ["unresolved", "Ni GPS ni code fiable", "Faible - exclu du Gold"],
        ],
        [35, 95, 50],
    )
    pdf.h2("Tests de regression")
    pdf.body(
        "Un ensemble de 118 tests pytest couvre les cas limites : code manquant, coordonnees nulles, "
        "valeurs hors plage, fallback reference vs reel, quotas API, auth JWT. Les tests sont "
        "executes a chaque push sur la branche feat/* (CI locale)."
    )

    # ── 17. Securite ───────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(17, "Securite de l'API et conformite RGPD")
    pdf.body(
        "La securite est traitee comme une contrainte de conception et non comme une couche "
        "ajoutee apres coup. Chaque composant expose une surface d'attaque reduite et ne "
        "revele aucune information interne en cas d'erreur."
    )
    pdf.h2("Authentification et autorisation")
    pdf.body(
        "L'API utilise des jetons JWT signes avec l'algorithme HS256 et une cle secrete "
        "chargee depuis la variable d'environnement JWT_SECRET (jamais en dur dans le code). "
        "Les jetons d'acces expirent apres 60 minutes ; les jetons de rafraichissement apres "
        "7 jours. La revocation est geree par une liste noire en base."
    )
    pdf.table(
        ["Role", "Acces", "Quotas par IP"],
        [
            ["Anonyme", "health, catalog, datamarts (lecture seule)", "120 req/min"],
            ["viewer", "Tous les GET, flux evenements", "600 req/min"],
            ["admin", "Tout + pipeline (ETL), purge", "600 req/min"],
        ],
        [28, 100, 52],
    )
    pdf.h2("Protection contre les attaques courantes")
    pdf.bullet("XSS : ", "aucune injection DOM dans l'interface ; les valeurs backend sont echappees avant affichage.")
    pdf.bullet("Injection : ", "Pydantic v2 valide tous les parametres d'entree avant qu'ils atteignent la base.")
    pdf.bullet("CORS : ", "origine du frontend en liste blanche (UDE_CORS_ORIGINS). Refus par defaut.")
    pdf.bullet("Stack traces : ", "jamais exposes cote client. Les erreurs 500 retournent un code d'erreur opaque.")
    pdf.bullet("Secrets : ", "variables d'environnement dans .env gitignore. Scan Gitleaks en pre-commit.")
    pdf.h2("Conformite RGPD")
    pdf.body(
        "Le projet ne collecte aucune donnee personnelle. Toutes les sources sont des donnees "
        "publiques ouvertes. Les seules donnees utilisateurs sont les jetons JWT (stockes en "
        "base sous forme de hash), sans profilage ni tracking. La suppression d'un compte "
        "supprime le jeton associe."
    )
    pdf.body(
        "Les donnees immobilieres (DVF) sont utilisees uniquement au niveau aggregate "
        "(prix median par arrondissement), sans aucune information permettant de "
        "retrouver une transaction individuelle."
    )

    # ── 18. Monitoring ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(18, "Monitoring et observabilite")
    pdf.body(
        "Un endpoint /metrics expose les metriques au format Prometheus. Le service prometheus "
        "dans Docker Compose les collecte toutes les 15 secondes. Ces metriques permettent "
        "de surveiller la sante du projet en production."
    )
    pdf.h2("Metriques exposees")
    pdf.table(
        ["Metrique", "Type", "Description"],
        [
            ["http_requests_total", "counter", "Nombre de requetes par methode, route, status"],
            ["http_request_duration_seconds", "histogram", "Distribution des temps de reponse"],
            ["etl_pipeline_runs_total", "counter", "Nombre de runs ETL (success/failure)"],
            ["etl_last_run_timestamp", "gauge", "Timestamp du dernier run ETL"],
            ["catalog_sources_total", "gauge", "Nombre de sources dans le catalogue (83)"],
            ["db_pool_connections", "gauge", "Connexions actives PostgreSQL"],
            ["streaming_events_total", "counter", "Evenements Kafka traites par type"],
        ],
        [60, 32, 88],
    )
    pdf.h2("Alertes")
    pdf.body(
        "Les regles d'alerte Prometheus sont definies dans monitoring/alerts.yml : "
        "alerte si le taux d'erreur HTTP depasse 5% sur 5 minutes, alerte si le pipeline "
        "ETL n'a pas tourne depuis plus de 24 heures, alerte si la latence p95 depasse "
        "100 ms (seuil de degradation de l'experience utilisateur)."
    )

    # ── 19. Analyse par arrondissement ─────────────────────────────────────
    pdf.add_page()
    pdf.h1(19, "Analyse des donnees par arrondissement")
    pdf.body(
        "A titre d'illustration, voici les valeurs de reference calculees pour quelques "
        "arrondissements representatifs. Ces valeurs sont issues des constantes de reference "
        "(DVF 2023 et INSEE Filosofi 2020 agregees par nos soins a partir des fichiers publics)."
    )
    pdf.table(
        ["Arrondissement", "Prix m2", "Rev. median", "Score global"],
        [
            ["75001 · Louvre", "13 200 EUR", "34 200 EUR", "62"],
            ["75006 · Luxembourg", "15 800 EUR", "45 200 EUR", "71"],
            ["75011 · Popincourt", "10 800 EUR", "31 800 EUR", "52"],
            ["75013 · Gobelins", "9 200 EUR", "27 200 EUR", "48"],
            ["75016 · Passy", "11 200 EUR", "44 500 EUR", "58"],
            ["75019 · Buttes-Chaumont", "8 500 EUR", "21 500 EUR", "41"],
            ["75020 · Menilmontant", "8 700 EUR", "22 800 EUR", "43"],
        ],
        [58, 36, 42, 34],
    )
    pdf.body(
        "L'interpretation de ces chiffres illustre la pertinence de l'indicateur m2_abordables : "
        "dans le 6eme, un menage au revenu median peut acquerir 45 200 / 15 800 = 2,86 m2 avec "
        "un an de revenu ; dans le 19eme, 21 500 / 8 500 = 2,53 m2. L'ecart est moins grand "
        "qu'on ne l'imagine car les prix et les revenus covarient partiellement."
    )
    pdf.h2("Distribution des sources par arrondissement")
    pdf.body(
        "Apres geocodage, la repartition des enregistrements Silver par arrondissement est "
        "globalement homogene pour les sources institutionnelles (ecoles, espaces verts, "
        "stations Velib). En revanche, les sources OSM montrent une forte concentration "
        "dans les arrondissements centraux (1er-4eme) et populaires (11eme, 18eme, 20eme), "
        "refletant la densite commerciale reelle de Paris."
    )
    pdf.body(
        "Cette asymetrie est documentee via le quality_flag et visible dans le dashboard : "
        "les arrondissements avec peu de sources geocodees affichent un environnement_count "
        "plus faible, ce qui se repercute mecaniquement sur le cadre_vie_idx. Un enrichissement "
        "futur des sources normalisees corrigerait ce biais."
    )

    # ── 20. Glossaire ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(20, "Glossaire et acronymes")
    pdf.table(
        ["Terme / Acronyme", "Definition"],
        [
            ["ADEME", "Agence de l'Environnement et de la Maitrise de l'Energie · source DPE"],
            ["ASGI", "Asynchronous Server Gateway Interface · protocole serveur Python async"],
            ["Bronze", "Couche 1 medaillon : donnee brute, inchangee apres ingestion"],
            ["CORS", "Cross-Origin Resource Sharing · politique d'acces API par domaine"],
            ["CSV", "Comma-Separated Values · format de fichier tabulaire"],
            ["DSFR", "Systeme de Design de l'Etat francais (design.numerique.gouv.fr)"],
            ["DPE", "Diagnostic de Performance Energetique"],
            ["DVF", "Demandes de Valeurs Foncieres · transactions immobilieres DGFiP"],
            ["ETL", "Extract, Transform, Load · processus d'ingestion des donnees"],
            ["GeoJSON", "Format JSON pour les donnees geographiques (OGC)"],
            ["Gold", "Couche 3 medaillon : datamarts calcules, prets pour l'analyse"],
            ["HDFS", "Hadoop Distributed File System"],
            ["IRIS", "Ilots Regroupes pour l'Information Statistique (INSEE)"],
            ["JWT", "JSON Web Token · format de jeton d'authentification"],
            ["KPI", "Key Performance Indicator · indicateur cle de performance"],
            ["OSM", "OpenStreetMap · base cartographique collaborative mondiale"],
            ["Parquet", "Format colonnaire compresse (Apache Foundation)"],
            ["Polars", "Librairie DataFrame Python, moteur Rust, tres performante"],
            ["RNCP", "Repertoire National des Certifications Professionnelles"],
            ["Silver", "Couche 2 medaillon : donnee normalisee, geocodee, filtrée"],
            ["SIS", "Secteur d'Information des Sols (BRGM/Georisques)"],
            ["TTL", "Time To Live · duree de vie d'un enregistrement (Cassandra)"],
            ["TSV", "Tab-Separated Values · format de sortie Overpass API"],
            ["WCAG", "Web Content Accessibility Guidelines (norme accessibilite web)"],
        ],
        [42, 138],
    )

    # ── 21. Bibliographie ──────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(21, "Bibliographie et sources de reference")
    pdf.h2("Standards et normes")
    pdf.bullet("DSFR 1.11 : ", "systeme de design de l'Etat francais. design.numerique.gouv.fr")
    pdf.bullet("WCAG 2.1 AA : ", "Web Content Accessibility Guidelines. W3C 2018.")
    pdf.bullet("OpenAPI 3.1 : ", "specification API REST. swagger.io/specification")
    pdf.bullet("RFC 7519 : ", "JSON Web Token (JWT). IETF 2015.")
    pdf.h2("Donnees utilisees")
    pdf.bullet("opendata.paris.fr : ", "jeux de donnees officiels de la Ville de Paris.")
    pdf.bullet("data.gouv.fr : ", "portail open data de l'Etat francais (DGFiP, ADEME, DGALN, ONISR).")
    pdf.bullet("data.education.gouv.fr : ", "annuaire des etablissements scolaires (MENJ).")
    pdf.bullet("OpenStreetMap : ", "base cartographique collaborative sous licence ODbL.")
    pdf.bullet("Geoportail IGN : ", "tuiles cartographiques officielles (WMTS Geoplateforme).")
    pdf.bullet("INSEE Filosofi 2020 : ", "revenus disponibles par carreau et par IRIS.")
    pdf.h2("Technologies")
    pdf.bullet("Polars 0.20+ : ", "Ritchie Vink et al. pola.rs")
    pdf.bullet("FastAPI 0.110+ : ", "Sebastian Ramirez. fastapi.tiangolo.com")
    pdf.bullet("Apache Kafka : ", "Apache Software Foundation. kafka.apache.org")
    pdf.bullet("Apache Cassandra : ", "Apache Software Foundation. cassandra.apache.org")
    pdf.bullet("FPDF2 : ", "librairie Python de generation PDF. py-pdf.github.io/fpdf2")
    pdf.bullet("python-pptx : ", "librairie Python de generation PPTX. python-pptx.readthedocs.io")
    pdf.body(
        "L'ensemble du code source du projet est disponible sur GitHub (repo Adam-Blf/urban-data-explorer). "
        "La branche feat/more-sources-auto-ingest contient l'ensemble des sources et du catalogue 83 jeux. "
        "La CI locale (pytest 118 tests) est executee a chaque commit."
    )

    # ── 22. Annexes ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(22, "Annexe - Catalogue complet des sources")
    pdf.body("Extrait du catalogue SourceSpec par famille (source_id, titre abrege, fournisseur).")
    pdf.table(
        ["source_id", "Famille", "Fournisseur"],
        [
            ["velib_stations", "mobilite", "opendata.paris.fr"],
            ["velib_realtime", "mobilite", "opendata.paris.fr"],
            ["pistes_cyclables", "mobilite", "opendata.paris.fr"],
            ["stationnement_points", "mobilite", "opendata.paris.fr"],
            ["bornes_recharge", "mobilite", "opendata.paris.fr"],
            ["arrets_idfm", "mobilite", "data.iledefrance-mobilites.fr"],
            ["comptages_velos", "mobilite", "opendata.paris.fr"],
            ["arrets_bus_osm", "mobilite", "OpenStreetMap"],
            ["stations_metro_osm", "mobilite", "OpenStreetMap"],
            ["ecoles_maternelles", "vie_quotidienne", "opendata.paris.fr"],
            ["ecoles_elementaires", "vie_quotidienne", "opendata.paris.fr"],
            ["colleges", "vie_quotidienne", "opendata.paris.fr"],
            ["lycees", "vie_quotidienne", "data.education.gouv.fr"],
            ["creches", "vie_quotidienne", "opendata.paris.fr"],
            ["pharmacies", "vie_quotidienne", "OpenStreetMap"],
            ["restaurants_osm", "vie_quotidienne", "OpenStreetMap"],
            ["marches", "vie_quotidienne", "opendata.paris.fr"],
            ["espaces_verts", "environnement", "opendata.paris.fr"],
            ["arbres_paris", "environnement", "opendata.paris.fr"],
            ["ilots_fraicheur", "environnement", "opendata.paris.fr"],
            ["logements_sociaux", "logement_urbanisme", "opendata.paris.fr"],
            ["dpe_logements", "logement_urbanisme", "data.gouv.fr (ADEME)"],
            ["dvf_transactions", "logement_urbanisme", "data.gouv.fr (DGFiP)"],
            ["monuments_historiques", "logement_urbanisme", "data.gouv.fr"],
        ],
        [55, 48, 77],
    )
    pdf.body(
        "... et 59 autres sources. Voir etl/catalog.py pour le catalogue complet (ALL_SOURCES, 83 entrees)."
    )

    # ── Interface ───────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(23, "Interface DSFR et accessibilite")
    pdf.body(
        "L'interface adopte le Systeme de Design de l'Etat francais (DSFR) : bleu France #000091, "
        "rouge Marianne #E1000F, police Marianne, bloc Republique Francaise. Ce choix ancre le "
        "projet dans une identite institutionnelle coherente avec son objet (donnees de la Ville de Paris)."
    )
    pdf.bullet("Fond de plan IGN : ", "tuiles officielles Geoplateforme (WMTS), projection WGS84, 5 niveaux de zoom.")
    pdf.bullet("Choroplethes : ", "echelle sequentielle bleu France (9 niveaux) pour les indices quantitatifs.")
    pdf.bullet("Comparatif : ", "deux arrondissements cote a cote avec ecart en points.")
    pdf.bullet("Theme clair/sombre : ", "bascule DSFR, persistee en localStorage. Contraste WCAG AA verifie.")
    pdf.bullet("Accessibilite : ", "labels ARIA sur tous les controles, focus visibles, prefers-reduced-motion respecte.")
    pdf.bullet("Responsive : ", "adapte mobile (375px) et tablette (768px).")
    light, dark = ROOT / "ude-light.png", ROOT / "ude-dark.png"
    y = pdf.get_y() + 3
    if light.exists():
        pdf.set_draw_color(*BORDER)
        pdf.rect(15, y, 88, 55)
        pdf.image(str(light), x=15, y=y, w=88)
    if dark.exists():
        pdf.set_draw_color(*BORDER)
        pdf.rect(107, y, 88, 55)
        pdf.image(str(dark), x=107, y=y, w=88)
    pdf.set_xy(15, y + 57)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*MENTION)
    pdf.cell(88, 5, "Theme clair · fond de plan IGN", align="C")
    pdf.cell(4, 5, "")
    pdf.cell(88, 5, "Theme sombre · accessibilite WCAG AA", align="C")

    # ── Resultats ───────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(24, "Resultats et validation")
    pdf.h2("Performance PostgreSQL sous charge")
    pdf.table(
        ["Metrique", "Resultat"],
        [
            ["Requetes traitees sans erreur", "500 sur 500 (taux = 100%)"],
            ["Debit moyen", "1 190 requetes par seconde"],
            ["Temps de reponse moyen", "1,80 ms"],
            ["Temps de reponse p95", "3,50 ms"],
            ["Contraintes d'integrite verifiees", "3 sur 3 PASSED"],
        ],
        [100, 80],
    )
    pdf.h2("Couverture des tests")
    pdf.table(
        ["Module teste", "Tests", "Resultat"],
        [
            ["ETL Silver/Gold (Polars)", "24 tests", "PASSED"],
            ["API endpoints", "28 tests", "PASSED"],
            ["Enrichissement (indicateurs Gold)", "16 tests", "PASSED"],
            ["Auth JWT et quotas", "18 tests", "PASSED"],
            ["Qualite ETL (flags)", "14 tests", "PASSED"],
            ["Geocodage et normalisation", "12 tests", "PASSED"],
            ["Resilience (load test)", "6 tests", "PASSED"],
            ["TOTAL", "118 tests", "118 PASSED / 0 FAILED"],
        ],
        [100, 30, 50],
    )
    pdf.h2("Catalogue final")
    pdf.kpi_row([("83", "sources integrees"), ("4", "familles"), ("30", "sources OSM"), ("118", "tests PASSED")])
    pdf.body(
        "L'interface adopte le Systeme de Design de l'Etat francais (DSFR) : bleu France #000091, "
        "rouge Marianne #E1000F, police Marianne, bloc Republique Francaise. Ce choix ancre le "
        "projet dans une identite institutionnelle coherente avec son objet (donnees de la Ville de Paris)."
    )
    pdf.bullet("Fond de plan IGN : ", "tuiles officielles Geoplateforme (WMTS), projection WGS84, 5 niveaux de zoom.")
    pdf.bullet("Choroplethes : ", "echelle sequentielle bleu France (9 niveaux) pour les indices quantitatifs.")
    pdf.bullet("Comparatif : ", "deux arrondissements cote a cote avec ecart en points.")
    pdf.bullet("Theme clair/sombre : ", "bascule DSFR, persistee en localStorage. Contraste WCAG AA verifie.")
    pdf.bullet("Accessibilite : ", "labels ARIA sur tous les controles, focus visibles, prefers-reduced-motion respecte.")
    pdf.bullet("Responsive : ", "adapte mobile (375px) et tablette (768px).")
    light, dark = ROOT / "ude-light.png", ROOT / "ude-dark.png"
    y = pdf.get_y() + 3
    if light.exists():
        pdf.set_draw_color(*BORDER)
        pdf.rect(15, y, 88, 55)
        pdf.image(str(light), x=15, y=y, w=88)
    if dark.exists():
        pdf.set_draw_color(*BORDER)
        pdf.rect(107, y, 88, 55)
        pdf.image(str(dark), x=107, y=y, w=88)
    pdf.set_xy(15, y + 57)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*MENTION)
    pdf.cell(88, 5, "Theme clair · fond de plan IGN", align="C")
    pdf.cell(4, 5, "")
    pdf.cell(88, 5, "Theme sombre · accessibilite WCAG AA", align="C")

    # ── 25. Grille RNCP ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(25, "Couverture de la grille RNCP40875 · Bloc 1")
    pdf.table(
        ["Competence", "Preuve dans le projet"],
        [
            ["C1.1 · Relationnel", "Schema etoile PostgreSQL + tests de charge (1190 req/s, p95 3,5 ms) + 3/3 contraintes"],
            ["C1.2 · NoSQL", "Cassandra events_by_type, TTL 7 j, partitionnement par type d'evenement"],
            ["C1.3 · Data Lake", "Parquet Bronze/Silver/Gold sur HDFS ; sources variees CSV/TSV/GZ"],
            ["C1.4 · Scalabilite", "Docker Compose 11 services, healthchecks, volumes persistants, mode local-first"],
            ["C2.1 · API", "FastAPI /docs + auth JWT roles (viewer/admin) + quotas par IP (120/600 req/min)"],
            ["C2.2 · Streaming", "Producteur/consommateur Kafka -> Cassandra ; flux Velib + chantiers temps reel"],
            ["C2.3 · Transformation", "Polars normalise 83 sources ; DVF + INSEE Filosofi reels fusionnes"],
            ["C2.4 · Optimisation", "Parquet Snappy, index PG, lru_cache, lazy frame Polars, p95 < 4 ms"],
        ],
        [35, 145],
    )
    pdf.body(
        "Le projet couvre integralement les 8 competences du Bloc 1. Chaque competence est "
        "demonstree par du code en production, des tests passes et des metriques mesurees."
    )

    # ── 26. Conclusion ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1(26, "Conclusion et perspectives")
    pdf.body(
        "Urban Data Explorer est un projet d'ingenierie des donnees complet qui transforme "
        "83 sources de donnees ouvertes en un observatoire socio-urbain de Paris. Il demontre "
        "une chaine de traitement complete (Bronze, Silver, Gold), un stockage multi-modele "
        "(PostgreSQL, Cassandra, Parquet/HDFS), une API documentee et securisee, un streaming "
        "temps reel et une interface aux standards de l'Etat."
    )
    pdf.quote(
        "Le projet repond au besoin initial : un decideur peut comparer deux arrondissements "
        "parisiens sur cinq indicateurs en quelques secondes, avec des donnees fraichies chaque "
        "dimanche automatiquement."
    )
    pdf.h2("Perspectives d'evolution")
    pdf.bullet("Donnes reelles completes : ", "activer le telechargement DVF et INSEE Filosofi en auto-ingestion pour passer data_source='real' sur tous les arrondissements.")
    pdf.bullet("Enrichissement catalogue : ", "ajouter les accidents de la route (BAAC-ONISR), les DPE bâtiment par bâtiment (ADEME), les aides a la renovation.")
    pdf.bullet("Deploiement cloud : ", "migrer vers un cluster Kubernetes (GKE ou Azure AKS) avec CI/CD automatise.")
    pdf.bullet("Alerting : ", "declencher une alerte Prometheus si la disponibilite Velib passe sous un seuil critique dans un arrondissement.")
    pdf.bullet("API publique : ", "ouvrir l'API a des tiers (chercheurs, associations) avec gestion des cles et des quotas par utilisateur.")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 10.5)
    pdf.set_text_color(*MENTION)
    pdf.multi_cell(0, 5.8,
                   "Merci de votre attention. Nous restons disponibles pour repondre a vos questions "
                   "et faire une demonstration en direct de l'outil.")

    out = ROOT / "rapport.pdf"
    pdf.output(str(out))
    print(f"Rapport genere : {out}  ({pdf.page_no()} pages)")


if __name__ == "__main__":
    main()
