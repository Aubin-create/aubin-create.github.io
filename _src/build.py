"""
Construction du site Agencement de la Sée.

Assemble les pages de _src/pages/ avec l'en-tête et le pied de page communs,
puis écrit des fichiers HTML statiques à la racine du dépôt (servis tels quels
par GitHub Pages). Génère aussi sitemap.xml, les redirections des anciennes
adresses, les variantes d'images et la liste des emplacements photo.

Utilisation, depuis la racine du dépôt :
    python _src/build.py

Le dossier _src/ n'est jamais publié : GitHub Pages (Jekyll) ignore les
dossiers dont le nom commence par « _ ».
"""
import hashlib
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "_src"
DOMAINE = "https://agencementdelasee.fr"
DOSSIER_PHOTOS = RACINE / "images" / "photos"

try:
    from PIL import Image
except ImportError:  # Pillow est facultatif : sans lui, pas de variantes d'images
    Image = None

TEL = "06 81 13 87 87"
TEL_LIEN = "tel:+33681138787"
EMAIL = "agencementdelasee@gmail.com"
ADRESSE = "La Gare - Sourdeval, 50150 Sourdeval"

# Anciennes adresses du site -> nouvelles adresses
REDIRECTIONS = {
    "mentions-legales.html": "/mentions-legales/",
    "confidentialite.html": "/politique-de-confidentialite/",
}

def lire_json(nom):
    return json.loads((SRC / "data" / nom).read_text(encoding="utf-8"))

PHOTOS = {k: v for k, v in lire_json("photos.json").items() if not k.startswith("_")}
REALISATIONS = lire_json("realisations.json")["realisations"]
FAQ = lire_json("faq.json")["categories"]

CATEGORIES = {
    "plafonds": ("Plafonds tendus", "/plafonds-tendus-barrisol/"),
    "sols": ("Sols souples PVC", "/sols-pvc/"),
    "menuiseries": ("Menuiseries intérieures", "/menuiseries-interieures/"),
}

esc = lambda s: html.escape(s, quote=True)


def version(chemin):
    """Empreinte du fichier, ajoutée à son adresse pour forcer le rechargement après une mise à jour."""
    return chemin + "?v=" + hashlib.md5((RACINE / chemin.lstrip("/")).read_bytes()).hexdigest()[:8]


# =========================================================
# IMAGES
# =========================================================
def preparer_images():
    """Convertit les photos sources en WebP et crée les variantes 800 px."""
    if Image is None:
        print("! Pillow absent : variantes d'images non générées")
        return
    DOSSIER_PHOTOS.mkdir(parents=True, exist_ok=True)
    for ident, p in PHOTOS.items():
        cible = DOSSIER_PHOTOS / f"{ident}.webp"
        if "source" in p and not cible.exists():
            img = Image.open(RACINE / p["source"]).convert("RGB")
            img.thumbnail((1600, 1600))
            img.save(cible, "WEBP", quality=78, method=6)
        if cible.exists():
            petite = DOSSIER_PHOTOS / f"{ident}-800.webp"
            with Image.open(cible) as img:
                if img.width > 1000 and (not petite.exists() or petite.stat().st_mtime < cible.stat().st_mtime):
                    copie = img.convert("RGB")
                    copie.thumbnail((800, 2000))
                    copie.save(petite, "WEBP", quality=76, method=6)
    # Image de partage (réseaux sociaux) 1200 x 630
    og = RACINE / "images" / "partage.jpg"
    if not og.exists():
        img = Image.open(RACINE / PHOTOS["plafond-imprime-boutique"]["source"]).convert("RGB")
        ratio = 1200 / 630
        h = int(img.width / ratio)
        haut = max(0, (img.height - h) // 3)
        img.crop((0, haut, img.width, haut + h)).resize((1200, 630)).save(og, "JPEG", quality=82, optimize=True, progressive=True)


def dimensions(ident):
    f = DOSSIER_PHOTOS / f"{ident}.webp"
    if Image is not None and f.exists():
        with Image.open(f) as img:
            return img.width, img.height
    return PHOTOS[ident]["largeur"], PHOTOS[ident]["hauteur"]


def photo_presente(ident):
    return (DOSSIER_PHOTOS / f"{ident}.webp").exists()


def resoudre(ident):
    """Renvoie l'identifiant réellement affichable (photo, sinon sa photo de repli), ou None."""
    if photo_presente(ident):
        return ident
    repli = PHOTOS[ident].get("repli")
    if repli and photo_presente(repli):
        return repli
    return None


EMPLOIS = {}  # identifiant -> pages qui l'utilisent (pour la liste des emplacements)


def balise_img(ident, sizes="100vw", eager=False, classe=""):
    l, h = dimensions(ident)
    src = f"/images/photos/{ident}.webp"
    srcset = ""
    if (DOSSIER_PHOTOS / f"{ident}-800.webp").exists():
        srcset = f' srcset="/images/photos/{ident}-800.webp 800w, {src} {l}w" sizes="{sizes}"'
    charge = 'fetchpriority="high"' if eager else 'loading="lazy"'
    cls = f' class="{classe}"' if classe else ""
    return (f'<img{cls} src="{src}"{srcset} width="{l}" height="{h}" '
            f'alt="{esc(PHOTOS[ident]["alt"])}" {charge} decoding="async">')


def attente(ident, classe=""):
    """Emplacement d'une photo pas encore fournie."""
    p = PHOTOS[ident]
    return (f'<div class="photo-attente {classe}" data-photo="{ident}" data-alt="{esc(p["alt"])}" '
            f'data-dim="{p["largeur"]} × {p["hauteur"]}" data-consigne="{esc(p.get("consigne", ""))}">'
            f'<span class="photo-attente-texte">Photo à venir</span></div>')


def macro_photo(args, page):
    ident, *opts = args
    EMPLOIS.setdefault(ident, set()).add(page["chemin"])
    eager = "eager" in opts
    sizes = next((o[6:] for o in opts if o.startswith("sizes=")), "(min-width: 900px) 50vw, 100vw")
    classe = " ".join(o for o in opts if o != "eager" and not o.startswith("sizes="))
    reel = resoudre(ident)
    if reel:
        return f'<figure class="photo {classe}">{balise_img(reel, sizes, eager)}</figure>'
    return f'<figure class="photo photo--vide {classe}">{attente(ident)}</figure>'


# =========================================================
# GALERIE
# =========================================================
def element_galerie(r, page, interactif):
    ident = r["photo"]
    EMPLOIS.setdefault(ident, set()).add(page["chemin"])
    cat_nom, cat_url = CATEGORIES[r["categorie"]]
    taille = f' galerie-item--{r["taille"]}' if r.get("taille") else ""
    desc = f'<p>{esc(r["description"])}</p>' if r.get("description") else ""
    legende = (f'<figcaption><span class="galerie-cat">{cat_nom}</span>'
               f'<strong>{esc(r["titre"])}</strong>{desc}</figcaption>')
    if photo_presente(ident):
        visuel = balise_img(ident, "(min-width: 1100px) 33vw, (min-width: 640px) 50vw, 100vw")
        etat = ""
    else:
        if not interactif:
            return ""
        visuel = attente(ident)
        etat = " est-vide"
    if interactif:
        visuel = (f'<button type="button" class="galerie-ouvrir" aria-label="Agrandir : {esc(r["titre"])}">'
                  f'{visuel}</button>')
    return (f'<li class="galerie-item reveal{taille}{etat}" data-cat="{r["categorie"]}">'
            f'<figure>{visuel}{legende}</figure></li>')


def macro_galerie(args, page):
    if args and args[0]:
        cat = args[0]
        nombre = int(args[1]) if len(args) > 1 else 99
        items = [r for r in REALISATIONS if r["categorie"] == cat and photo_presente(r["photo"])][:nombre]
        if not items:
            return ('<p class="galerie-bientot">Les photos de nos chantiers seront publiées ici très prochainement. '
                    'En attendant, <a href="/contact/">contactez-nous</a> : nous pouvons vous montrer des exemples.</p>')
        return ('<ul class="galerie galerie--extrait">'
                + "".join(element_galerie(r, page, False) for r in items) + "</ul>")
    boutons = ['<button type="button" class="filtre" aria-pressed="true" data-filtre="tous">Toutes</button>']
    for cle, (nom, _) in CATEGORIES.items():
        boutons.append(f'<button type="button" class="filtre" aria-pressed="false" data-filtre="{cle}">{nom}</button>')
    return (f'<div class="filtres" role="group" aria-label="Filtrer les réalisations par prestation">{"".join(boutons)}</div>'
            '<ul class="galerie" id="galerie">'
            + "".join(element_galerie(r, page, True) for r in REALISATIONS)
            + '</ul><p class="galerie-vide" id="galerieVide" hidden>Les photos de cette prestation arrivent bientôt. '
              '<a href="/contact/">Parlez-nous de votre projet</a> : nous pouvons vous montrer des exemples.</p>')


# =========================================================
# FAQ
# =========================================================
def item_faq(q):
    return (f'<details class="faq-item"><summary><span>{esc(q["q"])}</span>'
            '<svg class="chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>'
            f'<div class="faq-reponse"><p>{q["r"]}</p></div></details>')


def macro_faq(args, page):
    if args and args[0] == "page":
        sommaire = "".join(f'<li><a href="#{c["id"]}">{c["titre"]}</a></li>' for c in FAQ)
        blocs = "".join(
            f'<section class="faq-bloc" id="{c["id"]}" aria-labelledby="titre-{c["id"]}">'
            f'<h2 id="titre-{c["id"]}">{c["titre"]}</h2><div class="faq-liste">'
            + "".join(item_faq(q) for q in c["questions"]) + "</div></section>"
            for c in FAQ)
        return (f'<div class="faq-page"><nav class="faq-sommaire" aria-label="Catégories de questions">'
                f'<p class="faq-sommaire-titre">Catégories</p><ul>{sommaire}</ul></nav>'
                f'<div class="faq-blocs">{blocs}</div></div>')
    # {{faq:categorie}} ou {{faq:categorie/id,categorie/id}}
    questions = []
    for sel in args[0].split(","):
        cat, _, ident = sel.partition("/")
        c = next(c for c in FAQ if c["id"] == cat)
        questions += [q for q in c["questions"] if not ident or q["id"] == ident]
    return '<div class="faq-liste">' + "".join(item_faq(q) for q in questions) + "</div>"


# =========================================================
# BLOCS RÉUTILISÉS
# =========================================================
ETAPES = [
    ("Prise de contact", "Vous nous présentez votre projet par téléphone ou via le formulaire : pièce, surface, envies, contraintes."),
    ("Étude du besoin", "Nous échangeons sur les possibilités — finition, éclairage, couleurs — et, si besoin, venons prendre les mesures sur place."),
    ("Devis détaillé", "Vous recevez un devis gratuit qui précise les matériaux et la pose. La date d'intervention est fixée ensemble."),
    ("Pose", "Intervention propre et sans gros travaux : une journée suffit pour un plafond tendu dans une pièce standard."),
    ("Réception du chantier", "Nous faisons le tour du résultat avec vous, vérifions les finitions et laissons la pièce prête à vivre."),
]


def macro_etapes(args, page):
    titre = args[0] if args and args[0] else "Comment se déroule votre projet"
    items = "".join(
        f'<li class="etape"><span class="etape-num" aria-hidden="true">{i:02d}</span>'
        f'<div><h3>{t}</h3><p>{d}</p></div></li>'
        for i, (t, d) in enumerate(ETAPES, 1))
    return (f'<section class="section section--creme" aria-labelledby="titre-etapes"><div class="conteneur etapes-grille">'
            f'<div class="etapes-texte"><p class="surtitre">Déroulement</p><h2 id="titre-etapes">{titre}</h2>'
            f'<ol class="etapes reveal">{items}</ol></div>'
            f'<div class="etapes-visuel reveal">{macro_photo(["plafond-pose-chantier", "photo--haute", "sizes=(min-width: 900px) 40vw, 100vw"], page)}</div>'
            '</div></section>')


def macro_cta(args, page):
    titre = args[0] if args and args[0] else "Un projet de plafond tendu ?"
    return (f'<section class="cta-final" aria-labelledby="titre-cta"><div class="conteneur cta-final-grille reveal">'
            f'<div><h2 id="titre-cta">{titre}</h2><p>Décrivez-nous votre pièce : nous revenons vers vous pour en parler '
            f'et établir un devis gratuit.</p></div><div class="cta-final-actions">'
            f'<a class="bouton bouton--plein" href="/contact/">Demander un devis</a>'
            f'<a class="bouton bouton--clair" href="{TEL_LIEN}">{TEL}</a></div></div></section>')


MACROS = {"photo": macro_photo, "galerie": macro_galerie, "faq": macro_faq,
          "etapes": macro_etapes, "cta": macro_cta}


def appliquer_macros(texte, page):
    def remplace(m):
        nom, args = m.group(1), m.group(2)
        liste = args.split("|") if args is not None else []
        if nom == "galerie" and liste:  # {{galerie:plafonds:3}}
            liste = liste[0].split(":")
        return MACROS[nom](liste, page)
    return re.sub(r"\{\{(\w+)(?::([^}]*))?\}\}", remplace, texte)


# =========================================================
# GABARIT COMMUN
# =========================================================
ICONE_TEL = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 '
             '19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 '
             '2 1.72c.13.95.33 1.88.6 2.78a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.27 '
             '1.83.47 2.78.6A2 2 0 0 1 22 16.92z"/></svg>')


def lien_nav(url, libelle, page, cle):
    actif = ' aria-current="page"' if page["chemin"] == url else ""
    classe = ' class="actif"' if page.get("nav") == cle else ""
    return f'<li><a href="{url}"{classe}{actif}>{libelle}</a></li>'


def entete(page):
    metiers_actif = ' class="actif"' if page.get("nav") == "metiers" else ""
    courant = ' aria-current="page"'
    sous = "".join(
        f'<li><a href="{url}"{courant if page["chemin"] == url else ""}>'
        f'<strong>{nom}</strong><span>{desc}</span></a></li>'
        for url, nom, desc in [
            ("/plafonds-tendus-barrisol/", "Plafonds tendus Barrisol", "Notre spécialité — installateur agréé"),
            ("/sols-pvc/", "Sols souples PVC", "Pièces de vie, chambres, pièces humides"),
            ("/menuiseries-interieures/", "Menuiseries intérieures", "Portes, placards, aménagements"),
        ])
    return f'''<a href="#principal" class="lien-evitement">Aller au contenu principal</a>
<header class="entete" id="entete">
  <div class="conteneur entete-barre">
    <a href="/" class="marque" aria-label="Agencement de la Sée — accueil">
      <img src="/images/logo.webp" width="156" height="120" alt="">
      <span class="marque-texte"><strong>Agencement de la Sée</strong><span>Plafonds tendus Barrisol · Sud Manche</span></span>
    </a>
    <button class="nav-bascule" id="navBascule" type="button" aria-expanded="false" aria-controls="navPrincipale">
      <span class="nav-bascule-barres" aria-hidden="true"><span></span><span></span><span></span></span>
      <span class="visuellement-cache">Menu</span>
    </button>
    <nav class="nav" id="navPrincipale" aria-label="Navigation principale">
      <ul class="nav-liste">
        {lien_nav("/", "Accueil", page, "accueil")}
        <li class="nav-deroulant">
          <button type="button" class="nav-deroulant-bouton" aria-expanded="false" aria-controls="sousMenuMetiers"><span{metiers_actif}>Nos métiers</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
          </button>
          <ul class="sous-menu" id="sousMenuMetiers">{sous}</ul>
        </li>
        {lien_nav("/realisations/", "Réalisations", page, "realisations")}
        {lien_nav("/a-propos/", "À propos", page, "a-propos")}
        {lien_nav("/faq/", "FAQ", page, "faq")}
        {lien_nav("/contact/", "Contact", page, "contact")}
      </ul>
      <div class="nav-actions">
        <a class="nav-tel" href="{TEL_LIEN}">{ICONE_TEL}<span>{TEL}</span></a>
        <a class="bouton bouton--plein bouton--petit" href="/contact/">Demander un devis</a>
      </div>
    </nav>
  </div>
</header>'''


def ariane(page):
    if not page.get("ariane"):
        return ""
    etapes = [("Accueil", "/")]
    for morceau in page["ariane"].split(" > "):
        nom, _, url = morceau.partition("=")
        etapes.append((nom.strip(), url.strip() or page["chemin"]))
    liens = []
    for i, (nom, url) in enumerate(etapes):
        if i == len(etapes) - 1:
            liens.append(f'<li><span aria-current="page">{nom}</span></li>')
        else:
            liens.append(f'<li><a href="{url}">{nom}</a></li>')
    page["_ariane"] = etapes
    return f'<nav class="ariane" aria-label="Fil d\'Ariane"><ol>{"".join(liens)}</ol></nav>'


def pied(page):
    return f'''<footer class="pied">
  <div class="conteneur">
    <div class="pied-haut">
      <div class="pied-marque">
        <img src="/images/logo.webp" width="156" height="120" alt="Logo Agencement de la Sée, installateur agréé Barrisol" loading="lazy">
        <p>Installateur agréé Barrisol à Sourdeval. Plafonds tendus dans le Sud Manche et en Normandie, ainsi que sols souples PVC et menuiseries intérieures.</p>
        <a class="bouton bouton--plein bouton--petit" href="/contact/">Demander un devis</a>
      </div>
      <div>
        <p class="pied-titre">Prestations</p>
        <ul class="pied-liens">
          <li><a href="/plafonds-tendus-barrisol/">Plafonds tendus Barrisol</a></li>
          <li><a href="/sols-pvc/">Sols souples PVC</a></li>
          <li><a href="/menuiseries-interieures/">Menuiseries intérieures</a></li>
          <li><a href="/realisations/">Réalisations</a></li>
        </ul>
      </div>
      <div>
        <p class="pied-titre">L'entreprise</p>
        <ul class="pied-liens">
          <li><a href="/a-propos/">À propos</a></li>
          <li><a href="/faq/">Questions fréquentes</a></li>
          <li><a href="/contact/">Contact et devis</a></li>
        </ul>
      </div>
      <div>
        <p class="pied-titre">Contact</p>
        <ul class="pied-liens pied-contact">
          <li><a href="{TEL_LIEN}">{TEL}</a></li>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li><span>{ADRESSE}</span></li>
          <li><span>Lundi – vendredi : 9h–12h / 14h–18h<br>Samedi : sur rendez-vous</span></li>
        </ul>
        <div class="reseaux">
          <a href="https://www.instagram.com/agencement_de_la_see/" target="_blank" rel="noopener" aria-label="Instagram d'Agencement de la Sée (nouvel onglet)">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1"/></svg>
          </a>
          <a href="https://www.facebook.com/AgencementDeLaSee" target="_blank" rel="noopener" aria-label="Facebook d'Agencement de la Sée (nouvel onglet)">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M14 9h3V6h-3a4 4 0 0 0-4 4v2H7v3h3v6h3v-6h3l1-3h-4v-2a1 1 0 0 1 1-1z"/></svg>
          </a>
        </div>
      </div>
    </div>
    <div class="pied-bas">
      <span>© <span class="annee">{date.today().year}</span> Agencement de la Sée — SARL, Sourdeval (Manche)</span>
      <span class="pied-legal"><a href="/mentions-legales/">Mentions légales</a><span aria-hidden="true">·</span><a href="/politique-de-confidentialite/">Politique de confidentialité</a></span>
    </div>
  </div>
</footer>
<a class="appel-mobile" href="{TEL_LIEN}">{ICONE_TEL} Appeler le {TEL}</a>'''


# =========================================================
# DONNÉES STRUCTURÉES
# =========================================================
ENTREPRISE = {
    "@type": "HomeAndConstructionBusiness",
    "@id": f"{DOMAINE}/#entreprise",
    "name": "Agencement de la Sée",
    "description": "Installateur agréé Barrisol : pose de plafonds tendus dans le Sud Manche et en Normandie, ainsi que sols souples PVC et menuiseries intérieures.",
    "url": f"{DOMAINE}/",
    "logo": f"{DOMAINE}/images/logo.jpg",
    "image": f"{DOMAINE}/images/partage.jpg",
    "telephone": "+33681138787",
    "email": EMAIL,
    "address": {"@type": "PostalAddress", "streetAddress": "La Gare - Sourdeval", "addressLocality": "Sourdeval",
                "postalCode": "50150", "addressRegion": "Normandie", "addressCountry": "FR"},
    "openingHoursSpecification": [
        {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": "09:00", "closes": "12:00"},
        {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": "14:00", "closes": "18:00"},
    ],
    "areaServed": [{"@type": "City", "name": v} for v in
                   ["Sourdeval", "Mortain-Bocage", "Brécey", "Saint-Hilaire-du-Harcouët", "Vire Normandie"]]
                  + [{"@type": "AdministrativeArea", "name": "Manche"}, {"@type": "AdministrativeArea", "name": "Normandie"}],
    "knowsAbout": ["Plafond tendu", "Barrisol", "Sol souple PVC", "Menuiserie intérieure"],
    "sameAs": ["https://www.facebook.com/AgencementDeLaSee", "https://www.instagram.com/agencement_de_la_see/"],
}


def donnees_structurees(page):
    graphe = []
    if page.get("schema") in ("entreprise", "service"):
        graphe.append(ENTREPRISE)
    if page["chemin"] == "/":
        graphe.append({"@type": "WebSite", "@id": f"{DOMAINE}/#site", "url": f"{DOMAINE}/",
                       "name": "Agencement de la Sée", "inLanguage": "fr-FR",
                       "publisher": {"@id": f"{DOMAINE}/#entreprise"}})
    if page.get("schema") == "service":
        graphe.append({"@type": "Service", "name": page["service"], "serviceType": page["service"],
                       "url": DOMAINE + page["chemin"], "provider": {"@id": f"{DOMAINE}/#entreprise"},
                       "areaServed": [{"@type": "AdministrativeArea", "name": "Manche"},
                                      {"@type": "AdministrativeArea", "name": "Normandie"}]})
    if page.get("_ariane"):
        graphe.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i, "name": nom, "item": DOMAINE + url}
            for i, (nom, url) in enumerate(page["_ariane"], 1)]})
    if not graphe:
        return ""
    contenu = json.dumps({"@context": "https://schema.org", "@graph": graphe}, ensure_ascii=False, indent=1)
    return f'<script type="application/ld+json">\n{contenu}\n</script>'


# =========================================================
# ASSEMBLAGE D'UNE PAGE
# =========================================================
def lire_page(fichier):
    texte = fichier.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", texte, re.S)
    meta = {}
    for ligne in m.group(1).splitlines():
        cle, _, val = ligne.partition(":")
        meta[cle.strip()] = val.strip()
    meta["corps"] = texte[m.end():]
    return meta


def assembler(page):
    fil = ariane(page)
    corps = appliquer_macros(page["corps"].replace("{{ariane}}", fil), page)
    indexable = page.get("robots", "index") == "index"
    canon = DOMAINE + page["chemin"]
    image_og = DOMAINE + "/images/partage.jpg"
    robots = "" if indexable else '<meta name="robots" content="noindex, follow">\n'
    canonique = f'<link rel="canonical" href="{canon}">\n' if indexable else ""
    turnstile = ('<link rel="preconnect" href="https://challenges.cloudflare.com">\n'
                 '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>\n'
                 if page.get("formulaire") == "oui" else "")
    script_contact = (f'<script src="{version("/assets/js/contact.js")}" defer></script>\n'
                      if page.get("formulaire") == "oui" else "")
    precharge = ""
    if page.get("precharge"):
        reel = resoudre(page["precharge"])
        if reel:
            precharge = f'<link rel="preload" as="image" href="/images/photos/{reel}.webp" fetchpriority="high">\n'
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page["titre"])}</title>
<meta name="description" content="{esc(page["description"])}">
{robots}{canonique}<meta name="theme-color" content="#14161F">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/images/favicon.png">
<link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="Agencement de la Sée">
<meta property="og:title" content="{esc(page.get("og_titre", page["titre"]))}">
<meta property="og:description" content="{esc(page["description"])}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{image_og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Plafond tendu Barrisol imprimé posé par Agencement de la Sée">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Work+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap">
{precharge}<link rel="stylesheet" href="{version("/assets/css/site.css")}">
<script>document.documentElement.classList.add('js');</script>
<script src="{version("/assets/js/site.js")}" defer></script>
{script_contact}{turnstile}{donnees_structurees(page)}
</head>
<body class="{page.get("classe", "")}">
{entete(page)}
<main id="principal">
{corps.strip()}
</main>
{pied(page)}
</body>
</html>
'''


def chemin_sortie(chemin):
    if chemin.endswith(".html"):
        return RACINE / chemin.lstrip("/")
    return RACINE / chemin.strip("/") / "index.html" if chemin != "/" else RACINE / "index.html"


def page_redirection(cible):
    url = DOMAINE + cible
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Page déplacée — Agencement de la Sée</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={cible}">
</head>
<body>
<p>Cette page a été déplacée : <a href="{cible}">{url}</a>.</p>
</body>
</html>
'''


# =========================================================
# CONTRÔLES
# =========================================================
def verifier_liens(fichiers):
    erreurs = []
    for f in fichiers:
        texte = f.read_text(encoding="utf-8")
        for attr, cible in re.findall(r'\b(href|src)="(/[^"#?]*)', texte):
            if cible.startswith("//"):
                continue
            p = RACINE / cible.lstrip("/")
            if cible.endswith("/"):
                p = p / "index.html"
            if not p.exists():
                erreurs.append(f"{f.relative_to(RACINE)} -> {cible}")
        for ancre in re.findall(r'href="#([^"]+)"', texte):
            if f'id="{ancre}"' not in texte:
                erreurs.append(f"{f.relative_to(RACINE)} -> #{ancre} (ancre absente)")
    return erreurs


def liste_emplacements():
    lignes = ["# Emplacements photo", "",
              "Fichier généré par `_src/build.py` — ne pas modifier à la main.", "",
              "Pour chaque photo à venir : passez-la dans Squoosh (format WebP, qualité 75 environ,",
              "largeur indiquée), nommez-la exactement comme ci-dessous et déposez-la dans `images/photos/`.",
              "Elle s'affiche automatiquement à la place de l'emplacement « Photo à venir ».",
              "Relancez ensuite `python _src/build.py` pour l'inscrire dans le HTML (meilleur référencement).", "",
              "Astuce : ajoutez `?emplacements` à l'adresse d'une page (ex. https://agencementdelasee.fr/?emplacements)",
              "pour voir les emplacements encadrés sur le site.", "",
              "| Fichier à déposer | Dimensions conseillées | État | Utilisée sur | Consigne |",
              "|---|---|---|---|---|"]
    for ident, p in PHOTOS.items():
        etat = "présente" if photo_presente(ident) else ("à venir (photo de repli utilisée)" if resoudre(ident) else "**à venir**")
        pages = ", ".join(sorted(EMPLOIS.get(ident, []))) or "—"
        lignes.append(f'| `images/photos/{ident}.webp` | {p["largeur"]} × {p["hauteur"]} | {etat} | {pages} | {p.get("consigne", "")} |')
    (SRC / "EMPLACEMENTS-PHOTOS.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")


def main():
    preparer_images()
    pages = [lire_page(f) for f in sorted((SRC / "pages").glob("*.html"))]
    sorties = []
    for page in pages:
        sortie = chemin_sortie(page["chemin"])
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(assembler(page), encoding="utf-8")
        sorties.append(sortie)
    for ancien, nouveau in REDIRECTIONS.items():
        (RACINE / ancien).write_text(page_redirection(nouveau), encoding="utf-8")

    aujourd_hui = date.today().isoformat()
    urls = "".join(f"  <url><loc>{DOMAINE}{p['chemin']}</loc><lastmod>{aujourd_hui}</lastmod></url>\n"
                   for p in pages if p.get("robots", "index") == "index" and p.get("sitemap", "oui") == "oui")
    (RACINE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n", encoding="utf-8")

    liste_emplacements()
    erreurs = verifier_liens(sorties)
    print(f"{len(sorties)} pages générées.")
    if erreurs:
        print("Liens internes cassés :")
        for e in erreurs:
            print("  -", e)
        sys.exit(1)
    print("Aucun lien interne cassé.")


if __name__ == "__main__":
    main()
