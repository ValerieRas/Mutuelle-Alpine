"""
Générateur de données synthétiques — Mutuelle Alpine Assurances (MAA)
Cas fil rouge : détection de fraude aux sinistres (auto + habitation).

TOUTES LES DONNÉES SONT FICTIVES. Aucune personne réelle n'est représentée.

Le jeu contient VOLONTAIREMENT :
  - des données personnelles (nom, email, téléphone, IBAN, date de naissance) -> exercices RGPD / pseudonymisation
  - des défauts de qualité (doublons, dates incohérentes, montants négatifs ou au format texte, champs manquants)
  - un biais de sélection historique : les dossiers des jeunes assurés et des zones rurales ont été
    davantage enquêtés => davantage de fraudes "confirmées" chez eux (biais dans le label, pas dans la réalité)
  - un lot "mois suivant" présentant une dérive (inflation des montants, épisode de grêle, nouveau canal chatbot)

Usage :
    python data/generator/generate_data.py --seed 42 --out data/raw
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

PRENOMS_F = ["Camille", "Léa", "Manon", "Chloé", "Emma", "Inès", "Sarah", "Julie", "Laura", "Anaïs",
             "Nadia", "Fatima", "Claire", "Sophie", "Elodie", "Yasmine", "Lucie", "Margaux", "Aïcha", "Pauline"]
PRENOMS_H = ["Lucas", "Hugo", "Thomas", "Nicolas", "Karim", "Antoine", "Julien", "Maxime", "Mehdi", "Paul",
             "Romain", "Kevin", "Yanis", "Pierre", "Bastien", "Sofiane", "Florian", "Adrien", "Louis", "Rayan"]
NOMS = ["Martin", "Bernard", "Dubois", "Moreau", "Laurent", "Girard", "Roux", "Fournier", "Morel", "Mercier",
        "Blanc", "Guerin", "Muller", "Faure", "Chevalier", "Garnier", "Benali", "Rousseau", "Perrin", "Bonnet",
        "Fabre", "Brun", "Gauthier", "Henry", "Meunier", "Haddad", "Arnaud", "Collet", "Rey", "Vidal"]
# (code postal, commune, zone)
COMMUNES = [
    ("38000", "Grenoble", "urbaine"), ("38100", "Grenoble", "urbaine"), ("38400", "Saint-Martin-d'Hères", "urbaine"),
    ("38130", "Échirolles", "urbaine"), ("38240", "Meylan", "periurbaine"), ("38330", "Montbonnot", "periurbaine"),
    ("38500", "Voiron", "periurbaine"), ("38430", "Moirans", "periurbaine"), ("38170", "Seyssinet-Pariset", "periurbaine"),
    ("38250", "Villard-de-Lans", "rurale"), ("38350", "La Mure", "rurale"), ("38520", "Bourg-d'Oisans", "rurale"),
    ("38710", "Mens", "rurale"), ("38880", "Autrans-Méaudre", "rurale"), ("73000", "Chambéry", "urbaine"),
    ("73200", "Albertville", "periurbaine"), ("73300", "Saint-Jean-de-Maurienne", "rurale"), ("26000", "Valence", "urbaine"),
]
CSP = ["cadre", "employe", "ouvrier", "artisan_commercant", "etudiant", "retraite", "profession_intermediaire", "sans_activite"]

TYPES_AUTO = ["collision", "bris_de_glace", "vol", "vandalisme", "incendie_vehicule"]
TYPES_HAB = ["degat_des_eaux", "cambriolage", "incendie", "bris_de_glace_hab", "tempete_grele"]

DESC = {
    "collision": ["Accrochage sur le parking du supermarché, pare-choc arrière enfoncé.",
                  "Collision à un carrefour avec un véhicule qui n'a pas respecté la priorité.",
                  "Choc à faible vitesse en marche arrière contre un poteau.",
                  "Véhicule percuté à l'arrêt au feu rouge, le tiers a signé un constat."],
    "bris_de_glace": ["Pare-brise fissuré suite à une projection de gravillon sur l'A48.",
                      "Impact sur le pare-brise sur la route de Chamrousse.",
                      "Vitre latérale brisée sans cause identifiée."],
    "vol": ["Véhicule volé dans la nuit devant le domicile, clés en ma possession.",
            "Vol du véhicule sur le parking de la gare, plainte déposée.",
            "Vol de la voiture pendant un séjour au ski, retrouvée incendiée."],
    "vandalisme": ["Rayures sur toute la carrosserie et rétroviseurs arrachés.",
                   "Pneus crevés et carrosserie rayée dans la rue."],
    "incendie_vehicule": ["Départ de feu dans le compartiment moteur sur l'autoroute.",
                          "Véhicule incendié dans la nuit sur la voie publique."],
    "degat_des_eaux": ["Fuite du chauffe-eau ayant endommagé le parquet du séjour.",
                       "Infiltration depuis l'appartement du dessus, plafond taché.",
                       "Rupture d'une canalisation dans la salle de bain."],
    "cambriolage": ["Porte fracturée pendant les vacances, vol d'ordinateurs et de bijoux.",
                    "Cambriolage en journée, téléviseur et console dérobés.",
                    "Effraction par la fenêtre, vol de matériel informatique haut de gamme."],
    "incendie": ["Départ de feu dans la cuisine, hotte et placards détruits.",
                 "Incendie d'origine électrique dans le garage."],
    "bris_de_glace_hab": ["Baie vitrée brisée par un ballon.", "Vitre de la porte d'entrée cassée."],
    "tempete_grele": ["Toiture endommagée par la grêle, tuiles cassées.", "Velux brisé par un épisode de grêle violent."],
}
# Textes "copiés-collés" d'un réseau de fraude organisé (indice détectable par embeddings / similarité)
DESC_RESEAU = [
    "Le véhicule a été heurté par un véhicule inconnu qui a pris la fuite, dégâts importants à l'avant et sur le côté droit.",
    "Vol avec effraction pendant notre absence, nombreux objets de valeur dérobés dont matériel informatique et bijoux de famille.",
]

PREFIXES = ["", "", "Bonjour,", "Ce matin,", "Hier soir,", "En rentrant du travail,", "Pendant le week-end,",
            "Je vous signale que", "Suite à notre appel,", "Comme convenu avec l'agence,"]
SUFFIXES = ["", "", "Merci de me recontacter rapidement.", "Je joins les photos.", "Le devis suivra.",
            "Je reste disponible pour l'expert.", "C'est la première fois que cela m'arrive.", "Un voisin peut en témoigner.",
            "Dégâts constatés rue des Alpes.", "J'ai déjà contacté un réparateur.", "Plainte déposée au commissariat."]

LIEUX = ["avenue Jean Jaurès", "cours Berriat", "près de la gare", "quartier Championnet", "à la Bastille",
         "rue Félix Viallet", "zone commerciale de Comboire", "parking du Versoud", "centre-ville", "route de Lyon",
         "boulevard Gambetta", "près du campus", "rue de Stalingrad", "place Victor Hugo", "chemin des Granges"]

PLAFONDS = {"AUTO": {"tiers": 3000, "tiers_plus": 8000, "tous_risques": 25000},
            "HABITATION": {"essentielle": 10000, "confort": 30000, "premium": 80000}}


def rand_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def iban(rng: random.Random) -> str:
    return "FR76" + "".join(str(rng.randint(0, 9)) for _ in range(23))


def telephone(rng: random.Random) -> str:
    return "0" + str(rng.choice([6, 7])) + "".join(str(rng.randint(0, 9)) for _ in range(8))


def build(seed: int, n_assures: int, n_sinistres: int):
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    # ---------------- Assurés ----------------
    assures = []
    for i in range(1, n_assures + 1):
        sexe = rng.choice(["F", "M"])
        prenom = rng.choice(PRENOMS_F if sexe == "F" else PRENOMS_H)
        nom = rng.choice(NOMS)
        age = int(np.clip(np_rng.normal(46, 16), 18, 90))
        naissance = date(2026, 1, 1) - timedelta(days=age * 365 + rng.randint(0, 364))
        cp, commune, zone = rng.choices(COMMUNES, weights=[6, 5, 4, 4, 3, 2, 3, 2, 2, 1, 1, 1, 1, 1, 4, 2, 1, 3])[0]
        csp = "etudiant" if age < 24 and rng.random() < 0.6 else ("retraite" if age > 64 and rng.random() < 0.8 else rng.choice(CSP[:4] + CSP[6:]))
        email = f"{prenom.lower()}.{nom.lower()}{rng.randint(1, 99)}@{rng.choice(['mail.fr', 'courriel.com', 'exemple.net'])}"
        email = (email.replace("é", "e").replace("ë", "e").replace("ï", "i").replace("è", "e"))
        if rng.random() < 0.01:
            email = email.replace("@", "")  # défaut : email invalide
        assures.append(dict(id_assure=f"A{i:05d}", civilite="Mme" if sexe == "F" else "M.", prenom=prenom, nom=nom,
                            sexe=sexe, date_naissance=naissance.isoformat(), email=email, telephone=telephone(rng),
                            iban=iban(rng), code_postal=cp if rng.random() > 0.015 else None, commune=commune,
                            zone=zone, csp=csp,
                            date_adhesion=rand_date(rng, date(2012, 1, 1), date(2025, 6, 30)).isoformat()))
    df_a = pd.DataFrame(assures)

    # ---------------- Contrats ----------------
    contrats = []
    cid = 1
    for a in assures:
        produits = ["AUTO"] if rng.random() < 0.55 else (["HABITATION"] if rng.random() < 0.5 else ["AUTO", "HABITATION"])
        for p in produits:
            formule = rng.choice(list(PLAFONDS[p].keys()))
            debut = max(date.fromisoformat(a["date_adhesion"]), rand_date(rng, date(2018, 1, 1), date(2025, 9, 30)))
            age = 2026 - int(a["date_naissance"][:4])
            prime = (420 if p == "AUTO" else 260) * {"tiers": .7, "tiers_plus": 1, "tous_risques": 1.6,
                                                    "essentielle": .8, "confort": 1, "premium": 1.7}[formule]
            if p == "AUTO" and age < 25:
                prime *= 1.8
            contrats.append(dict(id_contrat=f"C{cid:06d}", id_assure=a["id_assure"], produit=p, formule=formule,
                                 date_debut=debut.isoformat(),
                                 date_fin=None if rng.random() < .85 else rand_date(rng, debut + timedelta(days=200), date(2026, 6, 30)).isoformat(),
                                 prime_annuelle=round(prime * rng.uniform(.85, 1.2), 2),
                                 franchise=rng.choice([0, 150, 300, 500]),
                                 plafond_garantie=PLAFONDS[p][formule]))
            cid += 1
    df_c = pd.DataFrame(contrats)

    # ---------------- Prestataires ----------------
    prest = []
    for i in range(1, 121):
        typ = "garage" if i <= 70 else "artisan"
        cp, commune, _ = rng.choice(COMMUNES)
        prest.append(dict(id_prestataire=f"P{i:04d}", raison_sociale=f"{rng.choice(['Garage', 'Carrosserie', 'Auto']) if typ == 'garage' else rng.choice(['Plomberie', 'Rénov', 'Multiservices'])} {rng.choice(NOMS)} {commune}",
                          type_prestataire=typ, code_postal=cp, agree_maa=rng.random() < .75,
                          siret="".join(str(rng.randint(0, 9)) for _ in range(14))))
    df_p = pd.DataFrame(prest)
    reseau_prest = {"P0013", "P0047", "P0088", "P0102"}  # prestataires impliqués dans un réseau
    df_p.loc[df_p.id_prestataire.isin(reseau_prest), "agree_maa"] = False

    # ---------------- Sinistres ----------------
    contrats_by_id = {c["id_contrat"]: c for c in contrats}
    assure_by_id = {a["id_assure"]: a for a in assures}
    cids = list(contrats_by_id)
    sinistres, enquetes = [], []
    reseau_assures = set(rng.sample([a["id_assure"] for a in assures], 45))

    def make_claim(k: int, start: date, end: date, drift: bool = False):
        c = contrats_by_id[rng.choice(cids)]
        a = assure_by_id[c["id_assure"]]
        if rng.random() < .03:  # forcer un membre du réseau
            a_id = rng.choice(sorted(reseau_assures))
            cs = [x for x in contrats if x["id_assure"] == a_id]
            c, a = rng.choice(cs), assure_by_id[a_id]
        debut = date.fromisoformat(c["date_debut"])
        surv = rand_date(rng, max(start, debut), end) if debut < end else end
        age = surv.year - int(a["date_naissance"][:4])
        in_reseau = a["id_assure"] in reseau_assures

        # ---- fraude "réelle" (inconnue de l'assureur)
        logit = -4.0 + 2.6 * in_reseau + 0.6 * ((surv - debut).days < 90) + rng.gauss(0, .6)
        fraude_reelle = rng.random() < 1 / (1 + np.exp(-logit))

        produit = c["produit"]
        types = TYPES_AUTO if produit == "AUTO" else TYPES_HAB
        w = None
        if drift and produit == "HABITATION":
            w = [1, 1, .5, .5, 6]  # épisode de grêle
        typ = rng.choices(types, weights=w)[0] if w else rng.choice(types)
        plafond = c["plafond_garantie"]
        base = {"collision": 1800, "bris_de_glace": 450, "vol": 9000, "vandalisme": 1200, "incendie_vehicule": 7000,
                "degat_des_eaux": 2600, "cambriolage": 4200, "incendie": 9000, "bris_de_glace_hab": 600, "tempete_grele": 3500}[typ]
        montant = min(plafond, max(80, np_rng.lognormal(np.log(base), .55)))
        if fraude_reelle:
            montant = min(plafond * rng.uniform(.82, .99), montant * rng.uniform(1.6, 2.8))
        if drift:
            montant *= 1.08  # inflation coûts de réparation
        delai = int(np_rng.exponential(4)) + (rng.randint(15, 60) if fraude_reelle and rng.random() < .45 else 0)
        decl = surv + timedelta(days=delai)
        heure = rng.randint(0, 5) if (fraude_reelle and rng.random() < .4) else rng.randint(6, 23)
        if fraude_reelle and rng.random() < .55:
            desc = rng.choice(DESC_RESEAU)
        else:
            # textes légitimes : rédigés par l'assuré => variés (contexte + fait + détail)
            desc = " ".join(x for x in [rng.choice(PREFIXES), rng.choice(DESC[typ]),
                                         f"C'était vers {heure}h, {rng.choice(LIEUX)}.", rng.choice(SUFFIXES)] if x)
        prest_pool = [p["id_prestataire"] for p in prest if p["type_prestataire"] == ("garage" if produit == "AUTO" else "artisan")]
        id_prest = rng.choice(sorted(reseau_prest)) if (fraude_reelle and in_reseau and rng.random() < .7) else rng.choice(prest_pool)
        canal = rng.choices(["application", "agence", "telephone", "chatbot"] if drift else ["application", "agence", "telephone"],
                            weights=[4, 2, 2, 3] if drift else [5, 3, 3])[0]
        s = dict(id_sinistre=f"S{k:07d}", id_contrat=c["id_contrat"], date_survenance=surv.isoformat(),
                 heure_survenance=heure, date_declaration=decl.isoformat(), type_sinistre=typ,
                 montant_declare=round(float(montant), 2), canal_declaration=canal, id_prestataire=id_prest,
                 description=desc, nb_tiers=rng.choice([0, 0, 1, 1, 2]) if produit == "AUTO" else 0,
                 temoins=(rng.random() < (.15 if fraude_reelle else .45)), photos_jointes=rng.choice([0, 1, 2, 3, 4, 6]) if not fraude_reelle else rng.choice([0, 0, 1, 2]),
                 constat_amiable=(produit == "AUTO" and rng.random() < (.2 if fraude_reelle else .5)),
                 _fraude_reelle=fraude_reelle, _age=age, _zone=a["zone"])
        return s

    for k in range(1, n_sinistres + 1):
        sinistres.append(make_claim(k, date(2023, 1, 1), date(2025, 12, 31)))

    # ---- Enquêtes : biais de sélection (plus d'enquêtes chez jeunes / ruraux)
    for s in sinistres:
        p_enq = .08 + .55 * (s["montant_declare"] > 6000) + .25 * s["_fraude_reelle"]
        p_enq += .18 * (s["_age"] < 26) + .12 * (s["_zone"] == "rurale")
        enq = rng.random() < min(p_enq, .95)
        if enq:
            detect = s["_fraude_reelle"] and rng.random() < .85
            # erreurs d'enquête plus fréquentes chez les jeunes et en zone rurale (préjugés humains historiques)
            faux_positif = (not s["_fraude_reelle"]) and rng.random() < (.03 + .10 * (s["_age"] < 26) + .06 * (s["_zone"] == "rurale"))
            enquetes.append(dict(id_sinistre=s["id_sinistre"],
                                 date_ouverture=(date.fromisoformat(s["date_declaration"]) + timedelta(days=rng.randint(1, 10))).isoformat(),
                                 date_cloture=(date.fromisoformat(s["date_declaration"]) + timedelta(days=rng.randint(20, 120))).isoformat(),
                                 conclusion="fraude_confirmee" if (detect or faux_positif) else "sinistre_legitime",
                                 enqueteur=rng.choice(["ENQ01", "ENQ02", "ENQ03", "ENQ04"])))

    # ---- Défauts de qualité injectés
    defects = []
    for s in rng.sample(sinistres, 60):   # date de déclaration antérieure à la survenance
        d = date.fromisoformat(s["date_survenance"]) - timedelta(days=rng.randint(1, 20))
        s["date_declaration"] = d.isoformat()
    for s in rng.sample(sinistres, 25):   # montant négatif
        s["montant_declare"] = -abs(s["montant_declare"])
    for s in rng.sample(sinistres, 30):   # montant au format texte FR
        s["montant_declare"] = f"{s['montant_declare']:.2f}".replace(".", ",")
    for s in rng.sample(sinistres, 20):   # contrat manquant
        s["id_contrat"] = None
    for s in rng.sample(sinistres, 15):   # type inconnu
        s["type_sinistre"] = rng.choice(["COLLISION", "autre", ""])
    defects += [dict(s) for s in rng.sample(sinistres, 80)]  # doublons (rejeu d'événements)
    sinistres_all = sinistres + defects
    rng.shuffle(sinistres_all)

    # ---- Lot du mois suivant (dérive)
    drift_batch = [make_claim(n_sinistres + 1000 + k, date(2026, 1, 1), date(2026, 1, 31), drift=True) for k in range(1, 801)]

    def clean(rows):
        return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]

    return df_a, df_c, df_p, clean(sinistres_all), pd.DataFrame(enquetes), clean(drift_batch), sinistres


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--assures", type=int, default=4000)
    ap.add_argument("--sinistres", type=int, default=12000)
    ap.add_argument("--out", default="data/raw")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df_a, df_c, df_p, sin, df_e, drift, truth = build(args.seed, args.assures, args.sinistres)
    df_a.to_csv(out / "assures.csv", index=False)
    df_c.to_csv(out / "contrats.csv", index=False)
    df_p.to_csv(out / "prestataires.csv", index=False)
    df_e.to_csv(out / "enquetes.csv", index=False)
    with open(out / "sinistres_events.jsonl", "w", encoding="utf-8") as f:
        for s in sin:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    with open(out / "sinistres_events_2026_01.jsonl", "w", encoding="utf-8") as f:
        for s in drift:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"assurés={len(df_a)} contrats={len(df_c)} prestataires={len(df_p)} événements={len(sin)} "
          f"enquêtes={len(df_e)} fraudes confirmées={int((df_e.conclusion == 'fraude_confirmee').sum())} lot_dérive={len(drift)}")


if __name__ == "__main__":
    main()
