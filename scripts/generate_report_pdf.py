"""Generation du rapport PDF de soutenance avec FPDF2."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Urban Data Explorer - Rapport de projet", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, "RNCP40875 - Bloc 1 - Expert en Ingenierie des donnees", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter(self, title: str, body: str):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, body)
        self.ln(4)


def main():
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.chapter("1. Contexte", (
        "Le projet Urban Data Explorer vise a construire un dashboard interactif "
        "pour explorer les donnees urbaines de Paris. Il integre un pipeline ETL "
        "(Bronze/Silver/Gold) avec Polars, une API FastAPI, et un frontend React/TypeScript "
        "avec MapBox (3D) et MapLibre (2D)."
    ))

    pdf.chapter("2. Architecture technique", (
        "- ETL: Polars (Python) pour le traitement Bronze/Silver/Gold\n"
        "- Stockage: PostgreSQL (relationnel, modele en etoile), Cassandra (NoSQL, streaming)\n"
        "- Data Lake: HDFS + Hive (DDL Bronze/Silver/Gold)\n"
        "- Streaming: Kafka (producteur/consommateur)\n"
        "- API: FastAPI avec authentification JWT, filtres geographiques\n"
        "- Frontend: React + TypeScript + MapBox GL JS (3D) + MapLibre GL JS (2D)\n"
        "- Orchestration: Docker Compose multi-profils"
    ))

    pdf.chapter("3. Sources de donnees", (
        "19 sources Open Data Paris couvrant 8 familles thematiques:\n"
        "Logement, Mobilite, Education, Culture, Sante, Espaces verts, "
        "Services publics, Pression urbaine.\n\n"
        "Geocodage offline via point-in-polygon (IRIS) + fallback API adresse.data.gouv.fr."
    ))

    pdf.chapter("4. Categories d'indicateurs et Score Global", (
        "1. Immobilier & Prix : Indices de prix au m2 moyen et volumes de ventes (DVF).\n"
        "2. Logement Social : Part (%) et volume des logements sociaux finances a Paris.\n"
        "3. Revenus & Socio-Eco : Revenu median disponible par menage (INSEE).\n"
        "4. Cadre de vie & Attractivite : Equilibre espaces verts, transports et accessibilite.\n"
        "5. Synthese globale (Score) : Moyenne ponderee des 4 indices de categories."
    ))

    pdf.chapter("5. Granularite cartographique", (
        "5 niveaux: Ville -> Arrondissement -> IRIS -> Rue -> Batiment\n"
        "Les elements non concernes sont grises automatiquement."
    ))

    output = ROOT / "rapport.pdf"
    pdf.output(str(output))
    print(f"Rapport genere: {output}")


if __name__ == "__main__":
    main()
