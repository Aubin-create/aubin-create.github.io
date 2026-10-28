# Site Agencement de la Sée — mode d'emploi

Le site est fait de fichiers HTML statiques servis par GitHub Pages. Ces fichiers sont **générés** à partir du dossier `_src/` (jamais publié) par un petit script Python.

```
_src/
  build.py              script de construction (lancer : python _src/build.py)
  pages/                contenu de chaque page (en-tête, pied de page et menu sont ajoutés automatiquement)
  data/photos.json      registre des photos et des emplacements à compléter
  data/realisations.json  galerie des réalisations
  data/faq.json         questions fréquentes (page FAQ + pages métiers)
  EMPLACEMENTS-PHOTOS.md  liste des photos attendues (générée)
assets/css/site.css     styles (couleurs de la marque en haut du fichier)
assets/js/site.js       menu, animations, galerie, emplacements photo
assets/js/contact.js    formulaire de devis (Worker Cloudflare + Turnstile)
images/photos/          photos du site, au format WebP
```

> Ne modifiez pas directement `index.html`, `plafonds-tendus-barrisol/index.html`, etc. : ils sont réécrits à chaque construction. Modifiez `_src/pages/…` puis relancez `python _src/build.py`.

## Ajouter une photo prévue (le plus simple)

1. Ouvrez `_src/EMPLACEMENTS-PHOTOS.md` (ou ajoutez `?emplacements` à l'adresse d'une page du site) pour voir le nom et les dimensions attendus.
2. Passez la photo dans [Squoosh](https://squoosh.app) : format **WebP**, qualité **75**, largeur indiquée (1600 px en général, 2400 px pour la grande photo d'accueil).
3. Nommez-la exactement comme indiqué, par exemple `sol-pvc-chambre.webp`, et déposez-la dans `images/photos/` (sur GitHub : *Add file → Upload files*).

La photo remplace automatiquement l'emplacement « Photo à venir », sans autre manipulation. Pour qu'elle soit aussi inscrite dans le code HTML (meilleur pour Google) et que sa version allégée 800 px soit créée, relancez ensuite `python _src/build.py` depuis un ordinateur.

## Ajouter une nouvelle réalisation à la galerie

1. Déclarez la photo dans `_src/data/photos.json` (identifiant, texte `alt`, dimensions).
2. Ajoutez une entrée dans `_src/data/realisations.json` : `photo`, `categorie` (`plafonds`, `sols` ou `menuiseries`), `titre`, `description`, et éventuellement `"taille": "large"` ou `"haute"`.
3. Déposez la photo dans `images/photos/`, puis lancez `python _src/build.py`.

Une réalisation dont la photo n'existe pas encore reste invisible pour les visiteurs.

## Construire et vérifier

```
python _src/build.py
```

Le script génère les pages, `sitemap.xml`, les redirections des anciennes adresses et la liste des emplacements photo, puis **vérifie qu'aucun lien interne n'est cassé** (il s'arrête avec une erreur sinon). Pillow (`pip install pillow`) est utilisé pour les variantes d'images ; sans lui le site se construit quand même.

Prévisualiser en local : `python -m http.server 8765` à la racine du dépôt, puis ouvrir http://127.0.0.1:8765/.

## Formulaire de devis

Navigateur → Worker Cloudflare (`workeragencelentdelasee…workers.dev`, vérifie Turnstile et les champs) → Make → Gmail / Google Sheets. Les noms des champs (`nom`, `email`, `telephone`, `sujet`, `date`, `message`, `consentement`, `site_web`, `cf-turnstile-response`) et les libellés de la liste « Prestation concernée » sont ceux attendus par le Worker : ne les modifiez pas sans adapter le Worker. Après un envoi réussi, le visiteur arrive sur `/contact/merci/` (page non indexée, utile pour compter les demandes).
