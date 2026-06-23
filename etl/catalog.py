"""Catalogue centralise des sources Open Data Paris.

Sources:
  - opendata.paris.fr (API Opendatasoft v2.1)
  - data.gouv.fr (CSV directs, DGFiP, ADEME, culture, sante)
  - data.education.gouv.fr (annuaire etablissements)
  - OpenStreetMap Overpass API (tout ce qui manque ailleurs)

Familles: 4 categories thematiques:
  mobilite | vie_quotidienne | environnement | logement_urbanisme

Sources OSM (OVERPASS: prefix): police, pompiers, pharmacies, culte,
  dentistes, medecins, restaurants, supermarches, banques, cinema,
  theatres, salles_sport, hotels, bacs_recyclage, terrains_sport,
  fontaines Wallace, parkings velos, autopartage, toilettes OSM.
"""

from __future__ import annotations

from dataclasses import dataclass

_ODP = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/{}/exports/csv?limit=-1&timezone=UTC&use_labels=false&epsg=4326"
_GVF = "https://www.data.gouv.fr/fr/datasets/{}"


@dataclass(frozen=True)
class SourceSpec:
    """Spécification d'une source de données Open Data."""

    source_id: str
    title: str
    family: str  # mobilite | vie_quotidienne | environnement | logement_urbanisme
    catalog_url: str
    download_url: str = ""
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
# Catalogue complet — 44 sources réparties en 4 familles thématiques
# ---------------------------------------------------------------------------

ALL_SOURCES: list[SourceSpec] = [

    # ========================================================================
    # 1. MOBILITE & ACCESSIBILITE
    # ========================================================================

    SourceSpec(
        source_id="velib_stations",
        title="Velib' - Localisation des stations",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/velib-emplacement-des-stations/",
        download_url=_ODP.format("velib-emplacement-des-stations"),
        geo_point_column="coordonnees_geo",
        arrondissement_candidates=("code_insee_commune", "nom_arrondissement_communes"),
    ),
    SourceSpec(
        source_id="velib_disponibilite",
        title="Velib' - Disponibilite temps reel",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/velib-disponibilite-en-temps-reel/",
        download_url=_ODP.format("velib-disponibilite-en-temps-reel"),
        geo_point_column="coordonnees_geo",
        arrondissement_candidates=("code_insee_commune", "nom_arrondissement_communes"),
    ),
    SourceSpec(
        source_id="amenagements_cyclables",
        title="Amenagements cyclables (pistes et bandes OSM)",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/amenagements-cyclables/",
        download_url=_ODP.format("amenagements-cyclables"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
    ),
    SourceSpec(
        source_id="stationnement_emplacements",
        title="Stationnement voie publique - Emplacements (points)",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/stationnement-voie-publique-emplacements/",
        download_url=_ODP.format("stationnement-voie-publique-emplacements"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrond",),
    ),
    SourceSpec(
        source_id="stationnement_emprises",
        title="Stationnement voie publique - Emprises (polygones)",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/stationnement-sur-voie-publique-emprises/",
        download_url=_ODP.format("stationnement-sur-voie-publique-emprises"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrond",),
    ),
    SourceSpec(
        source_id="belib",
        title="Belib' - Bornes recharge vehicules electriques (temps reel)",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel/",
        download_url=_ODP.format("belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel"),
        geo_point_column="coordonneesxy",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse_station",),
    ),
    SourceSpec(
        source_id="transit_stops",
        title="Points d'arret reseau Ile-de-France Mobilites",
        family="mobilite",
        catalog_url="https://data.iledefrance-mobilites.fr/explore/dataset/arrets/",
        download_url="https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/arrets/exports/csv?limit=-1",
        provider="IDFM / data.iledefrance-mobilites.fr",
        geo_point_column="arrgeopoint",
        arrondissement_candidates=("arrpostalregion",),
    ),
    SourceSpec(
        source_id="comptages_velos",
        title="Comptages velos - compteurs permanents Paris",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/comptage-velo-donnees-compteurs/",
        download_url=_ODP.format("comptage-velo-donnees-compteurs"),
        geo_point_column="coordonnees_geo",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("nom_compteur",),
    ),
    SourceSpec(
        source_id="chantiers_perturbants",
        title="Chantiers perturbants la circulation",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/chantiers-perturbants/",
        download_url=_ODP.format("chantiers-perturbants"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("cp_arrondissement",),
        address_candidates=("voie",),
    ),
    SourceSpec(
        source_id="voirie_paris",
        title="Voirie parisienne - emprises et noms de rues",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/voirie-emprises-des-voies/",
        download_url=_ODP.format("voirie-emprises-des-voies"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("libelle",),
    ),
    SourceSpec(
        source_id="wifi_paris",
        title="Points d'acces WiFi gratuits Paris",
        family="mobilite",
        catalog_url="https://opendata.paris.fr/explore/dataset/wifiparis/",
        download_url=_ODP.format("wifiparis"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="parkings_velos",
        title="Parkings et arceaux velos a Paris - OpenStreetMap",
        family="mobilite",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,capacity,covered;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=bicycle_parking](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="autopartage",
        title="Stations autopartage et taxis - OpenStreetMap",
        family="mobilite",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,operator;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[amenity=car_sharing](area.p);node[amenity=taxi](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),

    # ========================================================================
    # 2. VIE QUOTIDIENNE
    # ========================================================================

    # Education
    SourceSpec(
        source_id="maternelles",
        title="Ecoles maternelles de Paris",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/etablissements-scolaires-maternelles/",
        download_url=_ODP.format("etablissements-scolaires-maternelles"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arr_insee", "arr_libelle"),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="ecoles_elementaires",
        title="Ecoles elementaires de Paris",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/etablissements-scolaires-ecoles-elementaires/",
        download_url=_ODP.format("etablissements-scolaires-ecoles-elementaires"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arr_insee", "arr_libelle"),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="colleges",
        title="Colleges de Paris",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/etablissements-scolaires-colleges/",
        download_url=_ODP.format("etablissements-scolaires-colleges"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arr_insee", "arr_libelle"),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="lycees",
        title="Lycees et lycees professionnels de Paris - Annuaire education nationale",
        family="vie_quotidienne",
        catalog_url="https://data.education.gouv.fr/explore/dataset/fr-en-annuaire-education/",
        download_url="https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/exports/csv?limit=-1&where=code_postal%20like%20%2275%25%22%20and%20type_etablissement%20like%20%22Lyc%C3%A9e%25%22&timezone=UTC&use_labels=false",
        provider="Ministere Education / data.education.gouv.fr",
        separator=";",
        latitude_candidates=("latitude",),
        longitude_candidates=("longitude",),
        arrondissement_candidates=("code_postal",),
        address_candidates=("adresse_1",),
    ),
    SourceSpec(
        source_id="creches",
        title="Structures Petite Enfance - Creches et haltes garderies",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/structures-petite-enfance-paris/",
        download_url=_ODP.format("structures-petite-enfance-paris"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement", "code_postal"),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="bibliotheques",
        title="Bibliotheques de pret de la Ville de Paris",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/liste-des-bibliotheques-de-pret/",
        download_url=_ODP.format("liste-des-bibliotheques-de-pret"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    # Sante
    SourceSpec(
        source_id="defibrillateurs",
        title="Defibrillateurs installes a Paris",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/defibrillateurs/",
        download_url=_ODP.format("defibrillateurs"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("code_post", "commune"),
        address_candidates=("adr_post",),
    ),
    SourceSpec(
        source_id="sanisettes",
        title="Sanisettes - Toilettes publiques",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/sanisettesparis/",
        download_url=_ODP.format("sanisettesparis"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="hopitaux_idf",
        title="Etablissements hospitaliers franciliens (IDF)",
        family="vie_quotidienne",
        catalog_url=_GVF.format("les-etablissements-hospitaliers-franciliens-idf"),
        download_url="https://www.data.gouv.fr/fr/datasets/r/f14983e5-e5a8-4d75-8b2e-90b3f7beed3e",
        provider="ARS Ile-de-France / data.gouv.fr",
        separator=";",
        arrondissement_candidates=("code_postal",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="medecins_accredites",
        title="Medecins accredites par la HAS",
        family="vie_quotidienne",
        catalog_url=_GVF.format("medecins-accredites-par-la-has"),
        download_url="https://www.data.gouv.fr/fr/datasets/r/dc3a4890-f26e-4f17-a3c0-ad2a68e3c9a1",
        provider="HAS / data.gouv.fr",
        separator=";",
        arrondissement_candidates=("code_postal",),
        address_candidates=("adresse",),
    ),
    # Commerce & Services
    SourceSpec(
        source_id="marches_decouverts",
        title="Marches decouverts parisiens",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/marches-decouverts/",
        download_url=_ODP.format("marches-decouverts"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("ardt",),
        address_candidates=("localisation",),
    ),
    SourceSpec(
        source_id="commerces_semaest",
        title="Commerces Semaest (revitalisation commerciale)",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/commerces-semaest/",
        download_url=_ODP.format("commerces-semaest"),
        geo_point_column="xy",
        arrondissement_candidates=("cp",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="fontaines_a_boire",
        title="Fontaines a boire",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/fontaines-a-boire/",
        download_url=_ODP.format("fontaines-a-boire"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("commune",),
        address_candidates=("voie",),
    ),
    SourceSpec(
        source_id="equipements_sportifs",
        title="Equipements sportifs et bains de Paris",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/equipements-sportifs-bains-de-paris/",
        download_url=_ODP.format("equipements-sportifs-bains-de-paris"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="kiosques_presse",
        title="Kiosques a journaux de Paris",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/kiosques-a-journaux/",
        download_url=_ODP.format("kiosques-a-journaux"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="subventions_associations",
        title="Subventions accordees aux associations parisiennes",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/subventions-accordees-des-associations/",
        download_url=_ODP.format("subventions-accordees-des-associations"),
        arrondissement_candidates=("code_postal",),
        address_candidates=("nom_beneficiaire",),
    ),
    # Culture
    SourceSpec(
        source_id="que_faire_a_paris",
        title="Que faire a Paris - Agenda culturel et evenements",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/que-faire-a-paris-/",
        download_url=_ODP.format("que-faire-a-paris-"),
        geo_point_column="lat_lon",
        arrondissement_candidates=("address_zipcode",),
        address_candidates=("address_street",),
    ),
    SourceSpec(
        source_id="lieux_tournage",
        title="Lieux de tournage a Paris",
        family="vie_quotidienne",
        catalog_url="https://opendata.paris.fr/explore/dataset/lieux-de-tournage-a-paris/",
        download_url=_ODP.format("lieux-de-tournage-a-paris"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("ardt_lieu",),
        address_candidates=("adresse_lieu",),
    ),
    SourceSpec(
        source_id="musees_france",
        title="Liste des musees de France (referentiel national)",
        family="vie_quotidienne",
        catalog_url=_GVF.format("liste-des-musees-de-france"),
        download_url="https://www.data.gouv.fr/fr/datasets/r/16da7a4e-4bd5-4480-98ca-e0e3a5d79a5a",
        provider="Ministere de la Culture / data.gouv.fr",
        separator=";",
        latitude_candidates=("LATITUDE",),
        longitude_candidates=("LONGITUDE",),
        arrondissement_candidates=("CP",),
        address_candidates=("ADRESSE",),
    ),
    # Lieux de culte et pharmacies via OpenStreetMap Overpass API
    # (sources non disponibles sur opendata.paris.fr ni data.gouv.fr)
    SourceSpec(
        source_id="lieux_de_culte",
        title="Lieux de culte a Paris (eglises, mosquees, synagogues, temples) - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,religion,denomination;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=place_of_worship](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        arrondissement_candidates=(),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="pharmacies",
        title="Pharmacies a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,opening_hours,phone;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=pharmacy](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    # Securite & urgences (fills gap from source.MD)
    SourceSpec(
        source_id="commissariats",
        title="Commissariats et postes de police a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,operator;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=police](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="pompiers",
        title="Casernes de pompiers a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,operator;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=fire_station](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    # Sante complementaire OSM
    SourceSpec(
        source_id="dentistes",
        title="Dentistes et cabinets dentaires a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=dentist](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="medecins_gp",
        title="Medecins generalistes et cliniques a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[amenity=doctors](area.p);node[amenity=clinic](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="veterinaires",
        title="Veterinaires a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=veterinary](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    # Commerce quotidien
    SourceSpec(
        source_id="restaurants_cafes",
        title="Restaurants, cafes et restauration rapide a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,cuisine,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[amenity=restaurant](area.p);node[amenity=fast_food](area.p);node[amenity=cafe](area.p);node[amenity=bar](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="supermarches",
        title="Supermarches et epiceries a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,shop,operator,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[shop=supermarket](area.p);node[shop=convenience](area.p);node[shop=grocery](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="banques_dab",
        title="Banques et distributeurs automatiques a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,operator,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[amenity=bank](area.p);node[amenity=atm](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="bureaux_poste",
        title="Bureaux de poste et relais a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,operator,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=post_office](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    # Culture complementaire OSM
    SourceSpec(
        source_id="cinemas",
        title="Cinemas a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,operator,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=cinema](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="theatres",
        title="Theatres et salles de spectacle a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,operator;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[amenity=theatre](area.p);node[amenity=arts_centre](area.p);node[amenity=nightclub](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    # Sport & bien-etre
    SourceSpec(
        source_id="salles_sport",
        title="Salles de sport et fitness a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,leisure,sport,operator;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[leisure=fitness_centre](area.p);node[leisure=sports_centre](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    # Tourisme
    SourceSpec(
        source_id="hotels",
        title="Hotels et hebergements touristiques a Paris - OpenStreetMap",
        family="vie_quotidienne",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,tourism,stars,operator;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[tourism=hotel](area.p);node[tourism=hostel](area.p);node[tourism=apartment](area.p);node[tourism=guest_house](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),

    # ========================================================================
    # 3. ENVIRONNEMENT & CADRE DE VIE
    # ========================================================================

    SourceSpec(
        source_id="espaces_verts",
        title="Espaces verts parisiens (parcs, squares, promenades)",
        family="environnement",
        catalog_url="https://opendata.paris.fr/explore/dataset/espaces_verts/",
        download_url=_ODP.format("espaces_verts"),
        geo_point_column="geom_x_y",
        arrondissement_candidates=("adresse_codepostal",),
        address_candidates=("nom_ev",),
    ),
    SourceSpec(
        source_id="jardins_partages",
        title="Jardins partages parisiens",
        family="environnement",
        catalog_url="https://opendata.paris.fr/explore/dataset/jardins-partages/",
        download_url=_ODP.format("jardins-partages"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="ilots_fraicheur",
        title="Ilots de fraicheur - espaces verts frais (canicule)",
        family="environnement",
        catalog_url="https://opendata.paris.fr/explore/dataset/ilots-de-fraicheur-espaces-verts-frais/",
        download_url=_ODP.format("ilots-de-fraicheur-espaces-verts-frais"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="ilots_chaleur",
        title="Ilots de chaleur urbains - vulnerabilite par IRIS",
        family="environnement",
        catalog_url="https://opendata.paris.fr/explore/dataset/ilots-de-chaleur-vulnerabilite-par-iris/",
        download_url=_ODP.format("ilots-de-chaleur-vulnerabilite-par-iris"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
    ),
    SourceSpec(
        source_id="arbres_paris",
        title="Arbres de Paris (280 000+ arbres alignement et parcs)",
        family="environnement",
        catalog_url="https://opendata.paris.fr/explore/dataset/les-arbres/",
        download_url=_ODP.format("les-arbres"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="aires_jeux",
        title="Aires de jeux - elements d'equipement",
        family="environnement",
        catalog_url="https://opendata.paris.fr/explore/dataset/aires-de-jeux-elements-dequipement/",
        download_url=_ODP.format("aires-de-jeux-elements-dequipement"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="bruit_paris",
        title="Carte de bruit - indicateurs Lden 2022",
        family="environnement",
        catalog_url="https://opendata.paris.fr/explore/dataset/carte-de-bruit-lden-en-2022/",
        download_url=_ODP.format("carte-de-bruit-lden-en-2022"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
    ),
    SourceSpec(
        source_id="terrains_sport",
        title="Terrains de sport et installations exterieures a Paris - OpenStreetMap",
        family="environnement",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,leisure,sport,surface,access;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[leisure=pitch](area.p);node[leisure=track](area.p);node[leisure=swimming_pool][access!=private](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="bacs_recyclage",
        title="Points de recyclage et conteneurs tri selectif - OpenStreetMap",
        family="environnement",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,recycling_type;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[amenity=recycling](area.p);node[amenity=waste_basket](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="toilettes_osm",
        title="Toilettes publiques supplementaires - OpenStreetMap",
        family="environnement",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,access,wheelchair,opening_hours;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[amenity=toilets](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="fontaines_wallace",
        title="Fontaines Wallace et fontaines d'ornement - OpenStreetMap",
        family="environnement",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,amenity,historic,heritage;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;(node[amenity=drinking_water](area.p);node[historic=monument][name~\"Wallace\",i](area.p););out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),
    SourceSpec(
        source_id="stations_velo_osm",
        title="Pistes cyclables et voies vertes (geometrie) - OpenStreetMap",
        family="environnement",
        catalog_url="https://www.openstreetmap.org",
        download_url="OVERPASS:[out:csv(::lat,::lon,name,highway,bicycle,surface;true;\"\t\")][timeout:90];area[\"ref:INSEE\"=\"75056\"]->.p;node[highway=cycleway](area.p);out body;",
        provider="OpenStreetMap / Overpass API",
        separator="\t",
        latitude_candidates=("lat",),
        longitude_candidates=("lon",),
        address_candidates=("name",),
    ),

    # ========================================================================
    # 4. LOGEMENT & URBANISME
    # ========================================================================

    SourceSpec(
        source_id="logements_sociaux",
        title="Logements sociaux finances a Paris",
        family="logement_urbanisme",
        catalog_url="https://opendata.paris.fr/explore/dataset/logements-sociaux-finances-a-paris/",
        download_url=_ODP.format("logements-sociaux-finances-a-paris"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrdt", "code_postal"),
        address_candidates=("adresse_programme",),
    ),
    SourceSpec(
        source_id="dpe_paris",
        title="DPE - Diagnostics de Performance Energetique logements Paris (75)",
        family="logement_urbanisme",
        catalog_url=_GVF.format("dpe-v2-logements-existants"),
        download_url="https://www.data.gouv.fr/fr/datasets/r/6b0cd5ba-af0f-4e05-99de-5b8df5a39b5e",
        provider="ADEME / data.gouv.fr",
        separator=";",
        arrondissement_candidates=("code_insee_commune_actualise",),
        address_candidates=("adresse_ban",),
    ),
    SourceSpec(
        source_id="logements_vacants",
        title="Logements vacants taxables a Paris (LOVAC)",
        family="logement_urbanisme",
        catalog_url=_GVF.format("logements-vacants-du-parc-prive-par-anciennete-de-vacance-france-hors-mayotte"),
        download_url="https://www.data.gouv.fr/fr/datasets/r/c5069e8a-0286-4f4f-a3cb-06c32e58b6f0",
        provider="DGALN / data.gouv.fr",
        separator=";",
        arrondissement_candidates=("code_commune",),
    ),
    SourceSpec(
        source_id="permis_construire",
        title="Permis de construire deposes a Paris",
        family="logement_urbanisme",
        catalog_url="https://opendata.paris.fr/explore/dataset/permis-de-construire/",
        download_url=_ODP.format("permis-de-construire"),
        geo_point_column="geo_point_2d",
        arrondissement_candidates=("arrondissement",),
        address_candidates=("adresse",),
    ),
    SourceSpec(
        source_id="monuments_historiques",
        title="Immeubles proteges Monuments Historiques",
        family="logement_urbanisme",
        catalog_url=_GVF.format("immeubles-proteges-au-titre-des-monuments-historiques-2"),
        download_url="https://www.data.gouv.fr/fr/datasets/r/2e6e98d3-a527-4e14-a4a1-a948eedc20dd",
        provider="Ministere de la Culture / data.gouv.fr",
        separator=";",
        arrondissement_candidates=("CODE_INSEE",),
        address_candidates=("ADRESSE",),
    ),
    # Sources externes réelles (ETL spécialisé via etl/external.py)
    SourceSpec(
        source_id="dvf_transactions",
        title="DVF - Demandes de valeurs foncieres transactions 75 (2023)",
        family="logement_urbanisme",
        catalog_url="https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/75.csv.gz",
        download_url="https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/75.csv.gz",
        provider="DGFiP / data.gouv.fr",
        metadata_only=True,
    ),
    SourceSpec(
        source_id="filosofi_revenus",
        title="INSEE Filosofi - Revenu median disponible par IRIS (2020)",
        family="logement_urbanisme",
        catalog_url="https://www.insee.fr/fr/statistiques/7233950",
        provider="INSEE",
        metadata_only=True,
    ),
]

# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

SOURCE_MAP: dict[str, SourceSpec] = {s.source_id: s for s in ALL_SOURCES}

FAMILIES: dict[str, str] = {
    "mobilite":            "Mobilite & Accessibilite",
    "vie_quotidienne":     "Vie quotidienne",
    "environnement":       "Environnement & Cadre de vie",
    "logement_urbanisme":  "Logement & Urbanisme",
}

SOURCES_BY_FAMILY: dict[str, list[SourceSpec]] = {
    fam: [s for s in ALL_SOURCES if s.family == fam]
    for fam in FAMILIES
}
