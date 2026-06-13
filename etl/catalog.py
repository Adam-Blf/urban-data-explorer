"""Catalogue centralisé des sources Open Data Paris.

Chaque entrée décrit une source de données avec ses métadonnées, sa famille
thématique et les colonnes candidates pour l'extraction de coordonnées et
l'identification de l'arrondissement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpec:
    """Spécification d'une source de données Open Data Paris."""

    source_id: str
    title: str
    family: str  # green_space | mobility | public_service | education | culture | health | housing | pressure
    catalog_url: str
    provider: str = "Ville de Paris"
    metadata_only: bool = False
    separator: str = ";"
    encoding: str = "utf-8-sig"
    latitude_candidates: tuple[str, ...] = ()
    longitude_candidates: tuple[str, ...] = ()
    geo_point_column: str = ""
    arrondissement_candidates: tuple[str, ...] = ()
    address_candidates: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Catalogue des 24 sources, organisées par famille thématique
# ---------------------------------------------------------------------------

ALL_SOURCES: list[SourceSpec] = [
    # ── Logement ──────────────────────────────────────────────────────────
    SourceSpec(
        source_id="logements_sociaux",
        title="Logements sociaux finances a Paris",
        family="housing",
        catalog_url="https://opendata.paris.fr/explore/dataset/logements-sociaux-finances-a-paris/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrdt", "code_postal"),
        address_candidates=("adresse_programme",),
    ),

    # ── Mobilité ──────────────────────────────────────────────────────────
    SourceSpec(
        source_id="velib_stations",
        title="Velib' · Localisation des stations",
        family="mobility",
        catalog_url="https://opendata.paris.fr/explore/dataset/velib-disponibilite-en-temps-reel/",
        geo_point_column="coordonnees_geo",
        arrondissement_candidates=("code_insee_commune", "nom_arrondissement_communes"),
    ),
    SourceSpec(
        source_id="velib_disponibilite",
        title="Velib' · Disponibilite temps reel",
        family="mobility",
        catalog_url="https://opendata.paris.fr/explore/dataset/velib-disponibilite-en-temps-reel/",
        geo_point_column="coordonnees_geo",
        arrondissement_candidates=("code_insee_commune", "nom_arrondissement_communes"),
    ),
    SourceSpec(
        source_id="amenagements_cyclables",
        title="Amenagements cyclables",
        family="mobility",
        catalog_url="https://opendata.paris.fr/explore/dataset/amenagements-cyclables/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
    ),
    SourceSpec(
        source_id="stationnement_voie_publique_emplacements",
        title="Stationnement sur voie publique · Emplacements",
        family="mobility",
        catalog_url="https://opendata.paris.fr/explore/dataset/stationnement-voie-publique-emplacements/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrond",),
    ),
    SourceSpec(
        source_id="stationnement_voie_publique_emprises",
        title="Stationnement sur voie publique · Emprises",
        family="mobility",
        catalog_url="https://opendata.paris.fr/explore/dataset/stationnement-sur-voie-publique-emprises/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrond",),
    ),
    SourceSpec(
        source_id="belib",
        title="Belib' · Bornes de recharge electrique",
        family="mobility",
        catalog_url="https://opendata.paris.fr/explore/dataset/belib-points-de-recharge-pour-vehicules-electriques-donnees-statiques/",
        geo_point_column="coordonneesxy",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse_station",),
    ),
    SourceSpec(
        source_id="transit_stops",
        title="Points d'arret du reseau Ile-de-France Mobilites",
        family="mobility",
        catalog_url="https://data.iledefrance-mobilites.fr/explore/dataset/arrets/",
        geo_point_column="arrgeopoint",
        arrondissement_candidates=("arrpostalregion",),
    ),

    # ── Éducation ─────────────────────────────────────────────────────────
    SourceSpec(
        source_id="maternelles",
        title="Ecoles maternelles",
        family="education",
        catalog_url="https://opendata.paris.fr/explore/dataset/etablissements-scolaires-maternelles/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arr_insee", "arr_libelle"),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="ecoles_elementaires",
        title="Ecoles elementaires",
        family="education",
        catalog_url="https://opendata.paris.fr/explore/dataset/etablissements-scolaires-ecoles-elementaires/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arr_insee", "arr_libelle"),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="colleges",
        title="Colleges",
        family="education",
        catalog_url="https://opendata.paris.fr/explore/dataset/etablissements-scolaires-colleges/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arr_insee", "arr_libelle"),
        address_candidates=("adresse",),
    ),

    # ── Espaces verts ─────────────────────────────────────────────────────
    SourceSpec(
        source_id="espaces_verts",
        title="Espaces verts parisiens",
        family="green_space",
        catalog_url="https://opendata.paris.fr/explore/dataset/espaces_verts/",
        geo_point_column="geom_x_y",
        arrondissement_candidates=("adresse_codepostal",),
        address_candidates=("nom_ev",),
    ),

    # ── Culture ───────────────────────────────────────────────────────────
    SourceSpec(
        source_id="que_faire_a_paris",
        title="Que faire a Paris · Evenements culturels",
        family="culture",
        catalog_url="https://opendata.paris.fr/explore/dataset/que-faire-a-paris-/",
        geo_point_column="lat_lon",
        arrondissement_candidates=("address_zipcode",),
        address_candidates=("address_street",),
    ),

    # ── Santé ─────────────────────────────────────────────────────────────
    SourceSpec(
        source_id="sanisettesparis",
        title="Sanisettes · Toilettes publiques",
        family="health",
        catalog_url="https://opendata.paris.fr/explore/dataset/sanisettesparis/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),

    # ── Services publics ──────────────────────────────────────────────────
    SourceSpec(
        source_id="marches_decouverts",
        title="Marches decouverts",
        family="public_service",
        catalog_url="https://opendata.paris.fr/explore/dataset/marches-decouverts/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("ardt",),
        address_candidates=("localisation",),
    ),

    # ── Pression urbaine ──────────────────────────────────────────────────
    SourceSpec(
        source_id="chantiers_perturbants",
        title="Chantiers perturbants",
        family="pressure",
        catalog_url="https://opendata.paris.fr/explore/dataset/chantiers-perturbants/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("cp_arrondissement",),
        address_candidates=("voie",),
    ),

    # ── Sources ajoutees (equilibrage des familles) ─────────────────────────
    SourceSpec(
        source_id="defibrillateurs",
        title="Defibrillateurs installes a Paris",
        family="health",
        catalog_url="https://opendata.paris.fr/explore/dataset/defibrillateurs/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("code_post", "commune"),
        address_candidates=("adr_post",),
    ),
    SourceSpec(
        source_id="jardins_partages",
        title="Jardins partages",
        family="green_space",
        catalog_url="https://opendata.paris.fr/explore/dataset/jardins-partages/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="ilots_de_fraicheur",
        title="Ilots de fraicheur · espaces verts frais",
        family="green_space",
        catalog_url="https://opendata.paris.fr/explore/dataset/ilots-de-fraicheur-espaces-verts-frais/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="lieux_de_tournage",
        title="Lieux de tournage a Paris",
        family="culture",
        catalog_url="https://opendata.paris.fr/explore/dataset/lieux-de-tournage-a-paris/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("ardt_lieu",),
        address_candidates=("adresse_lieu",),
    ),
    SourceSpec(
        source_id="fontaines_a_boire",
        title="Fontaines a boire",
        family="public_service",
        catalog_url="https://opendata.paris.fr/explore/dataset/fontaines-a-boire/",
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("commune",),
        address_candidates=("voie",),
    ),
    SourceSpec(
        source_id="commerces_semaest",
        title="Commerces Semaest (revitalisation commerciale)",
        family="public_service",
        catalog_url="https://opendata.paris.fr/explore/dataset/commerces-semaest/",
        geo_point_column="xy",
        arrondissement_candidates=("cp",),
        address_candidates=("adresse",),
    ),

    # ── Sources externes reelles (chargees par etl/external.py) ─────────────
    SourceSpec(
        source_id="dvf_transactions",
        title="DVF · Demandes de valeurs foncieres (transactions immobilieres 75, 2023)",
        family="housing",
        catalog_url="https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/75.csv.gz",
        provider="DGFiP / data.gouv.fr",
        metadata_only=True,
    ),
    SourceSpec(
        source_id="filosofi_revenus",
        title="INSEE Filosofi · Revenu median disponible par IRIS (2020)",
        family="housing",
        catalog_url="https://www.insee.fr/fr/statistiques/7233950",
        provider="INSEE",
        metadata_only=True,
    ),
]

# Lookup rapide par source_id
SOURCE_MAP: dict[str, SourceSpec] = {s.source_id: s for s in ALL_SOURCES}

# Familles thématiques avec labels français
FAMILIES: dict[str, str] = {
    "green_space": "Espaces verts",
    "mobility": "Mobilite",
    "public_service": "Services publics",
    "education": "Education",
    "culture": "Culture",
    "health": "Sante",
    "housing": "Logement",
    "pressure": "Pression / travaux",
}
