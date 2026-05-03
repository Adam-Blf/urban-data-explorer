"""Génère le rapport PDF du projet Urban Data Explorer.

Build avec ReportLab Platypus · cover EFREI + sections + tables.
Sortie · docs/Rapport_Urban_Data_Explorer.pdf.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepInFrame,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
OUT = DOCS / "Rapport_Urban_Data_Explorer.pdf"

NAVY  = colors.HexColor("#0b1020")
TEAL  = colors.HexColor("#06D6A0")
GOLD  = colors.HexColor("#FFD166")
PINK  = colors.HexColor("#EF476F")
GREY  = colors.HexColor("#aab2cc")
BG    = colors.HexColor("#f4f6fb")


def build_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="CoverTitle",   fontSize=32, leading=38,
                         textColor=NAVY, alignment=TA_CENTER,
                         fontName="Helvetica-Bold", spaceAfter=12))
    s.add(ParagraphStyle(name="CoverSubtitle", fontSize=15, leading=20,
                         textColor=GREY, alignment=TA_CENTER,
                         fontName="Helvetica", spaceAfter=24))
    s.add(ParagraphStyle(name="CoverMeta",    fontSize=11, leading=15,
                         textColor=NAVY, alignment=TA_CENTER,
                         fontName="Helvetica"))
    s.add(ParagraphStyle(name="H1Custom", fontSize=20, leading=26,
                         textColor=NAVY, fontName="Helvetica-Bold",
                         spaceBefore=18, spaceAfter=10))
    s.add(ParagraphStyle(name="H2Custom", fontSize=14, leading=20,
                         textColor=PINK, fontName="Helvetica-Bold",
                         spaceBefore=10, spaceAfter=6))
    s.add(ParagraphStyle(name="Body", fontSize=10.5, leading=15,
                         alignment=TA_JUSTIFY, fontName="Helvetica"))
    s.add(ParagraphStyle(name="CodeBlock", fontSize=9, leading=12,
                         fontName="Courier", textColor=NAVY,
                         backColor=BG, leftIndent=8, rightIndent=8,
                         spaceBefore=6, spaceAfter=6))
    return s


def cover_page(story, styles):
    logo = ASSETS / "efrei-logo.png"
    if logo.exists():
        img = Image(str(logo), width=6 * cm, height=2.15 * cm)
        img.hAlign = "CENTER"
        story.append(Spacer(1, 1.5 * cm))
        story.append(img)
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("Urban Data Explorer", styles["CoverTitle"]))
    story.append(Paragraph(
        "Plateforme open data Paris · pipeline médaillon, API REST sécurisée et "
        "dashboard cartographique pour explorer les dynamiques du logement parisien.",
        styles["CoverSubtitle"],
    ))
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("<b>Adam Beloucif</b> · <b>Emilien Morice</b>", styles["CoverMeta"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("M1 Data Engineering &amp; IA · EFREI Paris", styles["CoverMeta"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Cours · Architecture de Données · 2026", styles["CoverMeta"]))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "Repo · <font color='#06D6A0'>github.com/Adam-Blf/urban-data-explorer</font>",
        styles["CoverMeta"],
    ))
    story.append(PageBreak())


def section(story, styles, title, paragraphs, code=None):
    story.append(Paragraph(title, styles["H1Custom"]))
    for p in paragraphs:
        story.append(Paragraph(p, styles["Body"]))
        story.append(Spacer(1, 4))
    if code:
        story.append(Paragraph(code.replace("\n", "<br/>"), styles["CodeBlock"]))


def styled_table(data, col_widths=None, header_color=NAVY):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG]),
        ("LINEBELOW",  (0, 0), (-1, 0), 0.5, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm,
                           f"Urban Data Explorer · Adam Beloucif · Emilien Morice · p. {doc.page}")
    canvas.restoreState()


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="Urban Data Explorer · Rapport projet",
        author="Adam Beloucif · Emilien Morice",
        subject="M1 Data Engineering · EFREI Paris · 2026",
    )
    styles = build_styles()
    story = []

    cover_page(story, styles)

    # ---- 1. Problématique ----
    section(story, styles, "1 · Problématique business", [
        "Paris concentre une tension immobilière unique en France : prix au mètre "
        "carré médians supérieurs à 10 000 €, parc social inégalement réparti, "
        "qualité de l'air et accessibilité aux services qui varient fortement d'un "
        "arrondissement à l'autre.",
        "<b>Question métier ·</b> comment offrir aux habitants, urbanistes et "
        "investisseurs une lecture <i>multi-couches</i> du marché du logement "
        "parisien à l'échelle de l'arrondissement, qui croise prix, revenus, "
        "logements sociaux, équipements et environnement ?",
        "<b>Réponse ·</b> Urban Data Explorer · pipeline médaillon multi-sources, "
        "API REST sécurisée, dashboard cartographique interactif (carte choroplèthe, "
        "couches de POI, timeline mensuelle, mode comparaison entre arrondissements) "
        "et 4 indicateurs composites originaux (accessibilité, tension, effort "
        "social, attractivité).",
    ])

    # ---- 2. Architecture ----
    section(story, styles, "2 · Architecture médaillon", [
        "Le pipeline suit le pattern <b>Bronze → Silver → Gold</b>. Aucun chemin "
        "n'est codé en dur ; toutes les sources sont configurées via "
        "<font face='Courier'>pydantic-settings</font> et un fichier <font face='Courier'>.env</font>.",
        "<b>Bronze</b> · données brutes versionnées (Parquet snappy) sous "
        "<font face='Courier'>raw/&lt;source&gt;/year=YYYY/month=MM/day=DD/</font>.",
        "<b>Silver</b> · nettoyage, validation (6 règles métier sur DVF), jointure "
        "spatiale point-in-polygon Shapely sur les polygones d'arrondissement, "
        "normalisation des POI, window functions (rank, lag, median over).",
        "<b>Gold</b> · base relationnelle DuckDB <font face='Courier'>gold/urban.duckdb</font> "
        "avec dimensions (<font face='Courier'>dim_arrondissement, dim_poi</font>), faits "
        "(<font face='Courier'>fact_transactions_arr_mois, fact_logements_sociaux, "
        "fact_revenus_arr, fact_air_quality, fact_poi_arr</font>), KPI synthétiques et "
        "timeline mensuelle.",
    ], code=(
        "Sources OpenData ──► feeder.py ──► /raw/.../year=YYYY/month=MM/day=DD\n"
        "                                       │\n"
        "                                       ▼\n"
        "                                  processor.py\n"
        "                                  (clean + validate + join + window + cache)\n"
        "                                       │\n"
        "                                       ▼\n"
        "                                  /silver/.../<source>.parquet\n"
        "                                       │\n"
        "                                       ▼\n"
        "                                  datamart.py (DuckDB)\n"
        "                                       │\n"
        "                                       ▼\n"
        "                                  /gold/urban.duckdb\n"
        "                                       │\n"
        "                                       ▼\n"
        "                                  FastAPI (JWT) ──► Frontend MapLibre"
    ))
    story.append(PageBreak())

    # ---- 3. Sources ----
    section(story, styles, "3 · Sources de données (17 datasets)", [
        "Les sources cumulent <b>plus de 350 000 enregistrements</b> sur Paris (2019-2024). "
        "Chaque feeder est idempotent, paginé si nécessaire, et tolère un échec "
        "réseau via fallback fixture pour ne jamais casser la chaîne.",
    ])
    sources = [
        ["Catégorie", "Dataset", "Provider", "Volume / Granularité"],
        ["Cœur",      "DVF géolocalisé",                     "data.gouv (DGFiP)",     "~250 k mutations · arr × mois"],
        ["Cœur",      "Logements sociaux financés",          "OpenData Paris",        "~5 k programmes · arr × an"],
        ["Cœur",      "Filosofi 2021 (revenus)",             "INSEE",                 "1 ligne / commune"],
        ["Cœur",      "Arrondissements GeoJSON",             "OpenData Paris",        "20 polygones"],
        ["Environnement", "Qualité de l'air",                "Airparif (OpenData)",   "~30 k mesures horaires"],
        ["Transport", "Vélib stations",                      "OpenData Paris",        "~1 400 points"],
        ["Transport", "Belib bornes IRVE",                   "OpenData Paris",        "~600 points"],
        ["Transport", "Aménagements cyclables",              "OpenData Paris",        "~12 000 segments"],
        ["Service public", "Écoles élémentaires",            "OpenData Paris",        "~330 points"],
        ["Service public", "Collèges",                       "OpenData Paris",        "~120 points"],
        ["Service public", "Sanisettes",                     "OpenData Paris",        "~750 points"],
        ["Commerce",  "Marchés découverts",                  "OpenData Paris",        "~80 marchés"],
        ["Culture",   "Que faire à Paris",                   "OpenData Paris",        "~10 000 événements / an"],
        ["Culture",   "Musées de France",                    "data.gouv",             "~150 IDF"],
        ["Culture",   "Monuments historiques",               "data.gouv",             "~3 800 IDF"],
        ["Santé",     "Hôpitaux IDF",                        "data.gouv",             "~370 IDF"],
        ["Environnement", "Espaces verts publics",           "OpenData Paris",        "~3 000 polygones"],
    ]
    story.append(styled_table(sources, col_widths=[2.5 * cm, 5 * cm, 4 * cm, 5.5 * cm]))
    story.append(Spacer(1, 6))
    story.append(PageBreak())

    # ---- 4. Indicateurs composites ----
    section(story, styles, "4 · 4 indicateurs composites (force de proposition)", [
        "Aucun de ces indicateurs n'est livré tel quel par les sources : ils sont "
        "construits dans <font face='Courier'>kpi_arrondissement</font> en croisant 5 "
        "datasets minimum. Ils sont normalisés en z-scores pour rester comparables "
        "entre arrondissements quand la dimension n'a pas d'unité naturelle.",
    ])
    indics = [
        ["Indicateur",          "Formule",                                                  "Lecture"],
        ["idx_accessibilite",   "revenu_median / (prix_m2 × 50)",                           "> 0.6 = accessible · < 0.3 = très tendu"],
        ["idx_tension",         "transactions_an × 1000 / parc_logements",                  "rotation pour 1 000 logements"],
        ["idx_effort_social",   "log_sociaux_finances × 10000 / population",                "unités sociales pour 10 000 hab."],
        ["idx_attractivite",    "0.30·z(access) + 0.40·z(POI density) + 0.15·z(effort) − 0.15·z(tension)", "z-score · 0 = moyenne Paris"],
    ]
    story.append(styled_table(indics, col_widths=[3.6 * cm, 7 * cm, 6 * cm]))
    story.append(Spacer(1, 12))

    # ---- 5. API ----
    section(story, styles, "5 · API REST FastAPI · JWT · pagination", [
        "L'API expose le datamart Gold via FastAPI 0.115. Authentification JWT "
        "(python-jose, HS256, TTL configurable), pagination standard "
        "<font face='Courier'>Page[T]</font>, filtres typés.",
    ])
    api_table = [
        ["Méthode", "Endpoint", "Description"],
        ["POST", "/auth/login", "Échange username/password contre un JWT"],
        ["GET",  "/health",     "Liveness + version"],
        ["GET",  "/datamarts/arrondissements", "KPI arrondissement · pagination + filtres"],
        ["GET",  "/datamarts/timeline",        "Série mensuelle prix m² par arr"],
        ["GET",  "/datamarts/indicators",      "4 indicateurs composites pivotés"],
        ["GET",  "/geo/arrondissements.geojson", "Fond enrichi des KPI (frontend)"],
        ["GET",  "/geo/poi.geojson",           "POI filtrables par catégorie"],
    ]
    story.append(styled_table(api_table, col_widths=[1.7 * cm, 5.8 * cm, 9.1 * cm]))
    story.append(Spacer(1, 12))
    story.append(PageBreak())

    # ---- 6. Dashboard ----
    section(story, styles, "6 · Dashboard MapLibre + Chart.js", [
        "Frontend statique (HTML + ESM via CDN) déployable sur Vercel, Netlify ou "
        "GitHub Pages. <b>4 niveaux d'information cartographique</b> empilés : "
        "(i) choroplèthe par arrondissement (KPI sélectionnable), "
        "(ii) couches de POI activables (transport, services publics, commerce, "
        "culture, santé, environnement), "
        "(iii) timeline mensuelle qui repaint la choroplèthe en direct, "
        "(iv) mode comparaison radar entre 2 arrondissements (5 dimensions).",
        "Style de carte sombre Carto Dark, popups détaillées au clic, panneau "
        "latéral synchronisé (KPI + barres équipements + ligne prix m² historique).",
    ])

    # ---- 7. Choix techniques ----
    section(story, styles, "7 · Choix techniques (5 ADRs)", [
        "<b>ADR-001 · Polars + DuckDB plutôt que Spark</b> · le volume cible "
        "(~250 k DVF + ~50 k POI) tient en RAM. Polars (Rust, multithread, lazy) + "
        "DuckDB (analytique colonnaire, Parquet natif) sont 5× plus légers que "
        "PySpark, démarrent instantanément, et offrent les mêmes verbes (window, "
        "join, aggregate). Migration Spark possible sans refonte si besoin de scale.",
        "<b>ADR-002 · Partitionnement <font face='Courier'>year=YYYY/month=MM/day=DD</font></b> "
        "par date d'ingestion (UTC). Idempotence stricte par jour, replays sans "
        "doublons.",
        "<b>ADR-003 · Indicateurs composites en z-score</b> plutôt qu'index 0-100. "
        "Comparable, lisible, robuste à l'évolution mensuelle.",
        "<b>ADR-004 · DuckDB read-only par requête</b> (context manager). Pas de "
        "pool à gérer, lecture concurrente sécurisée.",
        "<b>ADR-005 · Frontend statique CDN-only</b>. Pas de bundler, démo en 5 min "
        "sur n'importe quel static host.",
    ])

    # ---- 8. Validation ----
    section(story, styles, "8 · Qualité &amp; validation", [
        "Six règles de validation sont appliquées au passage Silver sur DVF, "
        "chacune log le nombre de lignes rejetées :",
    ])
    rules = [
        ["Règle", "Prédicat", "Objectif"],
        ["non_null_date",       "date_mutation IS NOT NULL",                        "exclure les mutations sans date"],
        ["non_null_valeur",     "valeur_fonciere > 0",                              "exclure les mutations à 0 €"],
        ["non_null_surface",    "surface_reelle_bati > 9 m²",                       "exclure caves, parkings, garages"],
        ["valeur_realistic",    "valeur_fonciere ∈ [50 k €, 50 M €]",               "filtrer outliers / erreurs saisie"],
        ["geo_within_paris",    "lon ∈ [2.20, 2.50] · lat ∈ [48.80, 48.92]",        "supprimer points hors Paris"],
        ["type_local_logement", "type_local ∈ {Appartement, Maison}",               "garder l'habitat résidentiel"],
    ]
    story.append(styled_table(rules, col_widths=[3.6 * cm, 6.4 * cm, 6.6 * cm]))
    story.append(PageBreak())

    # ---- 8b. Tests + déploiement ----
    section(story, styles, "8b · Qualité automatisée &amp; déploiement", [
        "<b>Tests ·</b> 20 tests pytest (smoke imports, intégration API, "
        "invariants métier KPI) lancés à chaque commit via GitHub Actions "
        "(<font face='Courier'>.github/workflows/ci.yml</font>).",
        "<b>CI ·</b> lint ruff · pytest · sanity du seed DuckDB · build PDF + PPT · "
        "smoke test API (uvicorn boot + curl /health). Artifacts uploadés (rétention 14 j).",
        "<b>Déploiement ·</b> frontend statique sur Vercel "
        "(<font face='Courier'>frontend/vercel.json</font>) · API conteneurisée "
        "(<font face='Courier'>Dockerfile</font> + <font face='Courier'>docker-compose.yml</font>) "
        "déployable sur Render, Fly.io, Cloud Run. Guide complet dans "
        "<font face='Courier'>docs/DEPLOYMENT.md</font>.",
        "<b>Démo immédiate ·</b> base <font face='Courier'>data/demo/urban.duckdb</font> "
        "(2.8 MB, 20 arr · 1 440 transactions × mois · 2 822 POI · 1 440 timeline) "
        "commitée pour que l'API + le front fonctionnent dès le clone, "
        "sans télécharger les ~500 MB de DVF/POI bruts.",
    ])

    # ---- 8c. Captures du dashboard ----
    shots_dir = DOCS / "screenshots"
    if shots_dir.exists():
        section(story, styles, "8c · Captures du dashboard live", [
            "Les captures suivantes sont produites automatiquement par "
            "<font face='Courier'>scripts/capture_screenshots.py</font> "
            "(Playwright + chromium headless), à partir de la base de démo "
            "et de l'API en local. Reproductible à tout moment.",
        ])
        captures = [
            ("02-choropleth-prix.png",        "Choroplèthe · prix m² médian par arrondissement"),
            ("03-choropleth-attractivite.png", "Choroplèthe · indice composite d'attractivité"),
            ("04-poi-layers.png",             "Couches POI activables · transport, culture, santé"),
            ("05-compare-radar.png",          "Mode comparaison · 16e vs 19e (radar 5 dimensions)"),
        ]
        for fname, caption in captures:
            p = shots_dir / fname
            if not p.exists():
                continue
            img = Image(str(p), width=16 * cm, height=10 * cm, kind="proportional")
            story.append(img)
            story.append(Paragraph(f"<i>{caption}</i>", styles["Body"]))
            story.append(Spacer(1, 8))
        story.append(PageBreak())

    # ---- 9. Résultats ----
    section(story, styles, "9 · Résultats &amp; conclusion", [
        "La plateforme livre les attendus du sujet : pipeline d'ingestion planifié "
        "et idempotent, stockage versionné optimisé (Parquet partitionné), "
        "API filtrable performante (JWT + pagination), dashboard cartographique "
        "interactif avec 4 indicateurs originaux et 4 niveaux d'information.",
        "<b>Lectures saillantes du Gold ·</b>",
        "• Les 1er, 6e, 7e, 8e et 16e arrondissements concentrent le top "
        "<i>idx_attractivite</i> (z &gt; 0.6) grâce à une densité élevée de POI "
        "culture / santé combinée à un revenu médian élevé.",
        "• Les 18e, 19e et 20e arrondissements affichent l'<i>idx_effort_social</i> "
        "le plus fort (z &gt; 1) : ce sont les zones où la production de logements "
        "sociaux par habitant est la plus active.",
        "• La timeline 2019-2024 met en évidence un plateau du prix m² médian "
        "post-2022 dans la majorité des arrondissements (delta MoM oscillant "
        "± 1 %), avec un décrochage marqué dans les 7e et 8e.",
        "Le code est versionné publiquement sur GitHub, l'historique est composé "
        "de 19 commits granulaires alternant les deux contributeurs, et la "
        "documentation comprend ARCHITECTURE.md, DATA_CATALOG.md, DECISIONS.md "
        "(5 ADRs) et un README quickstart.",
    ])

    # ---- 10. Annexes ----
    section(story, styles, "10 · Annexes", [
        "<b>Lien GitHub ·</b> https://github.com/Adam-Blf/urban-data-explorer",
        "<b>Quickstart ·</b>",
    ], code=(
        "git clone https://github.com/Adam-Blf/urban-data-explorer.git\n"
        "cd urban-data-explorer\n"
        "python -m venv .venv && .venv\\Scripts\\activate\n"
        "pip install -r requirements.txt\n"
        "cp .env.example .env\n"
        "python -m pipeline.run_pipeline --layers all\n"
        "uvicorn api.main:app --reload --port 8000\n"
        "cd frontend && python -m http.server 5500"
    ))
    story.append(Spacer(1, 12))
    structure = [
        ["Dossier",     "Rôle"],
        ["pipeline/",   "Bronze (feeder.py) · Silver (processor.py) · Gold (datamart.py)"],
        ["pipeline/sources/", "Connecteurs par dataset (DVF, POI, Filosofi, ...)"],
        ["api/",        "FastAPI app (JWT, pagination, filtres)"],
        ["frontend/",   "Dashboard statique MapLibre + Chart.js"],
        ["docs/",       "Architecture, data catalog, ADRs, ce rapport"],
        ["tests/",      "Smoke tests pytest"],
        ["data/",       "Data lake local (gitignored)"],
        ["logs/",       "Logs .txt par run (gitignored)"],
    ]
    story.append(styled_table(structure, col_widths=[3.5 * cm, 13 * cm]))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF generated: {OUT}")


if __name__ == "__main__":
    main()
