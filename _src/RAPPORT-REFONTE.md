# Refonte agencementdelasee.fr — compte rendu

*28 octobre 2026. Ce document n'est pas publié (le dossier `_src/` est ignoré par GitHub Pages).*

## 1. Audit du site existant

### Constats techniques (vérifiés)

| Point | État avant refonte |
|---|---|
| Hébergement | GitHub Pages, domaine `agencementdelasee.fr` (fichier `CNAME`), HTTPS actif |
| Pages indexables | 1 seule : `/` (page unique à ancres). `/index.html` sert le même contenu, sans balise canonique |
| Pages légales | `mentions-legales.html` et `confidentialite.html` en `noindex`… mais listées dans `sitemap.xml` (contradiction) |
| Balise canonique | Absente partout |
| Open Graph / partage | Absent |
| Titres | 1 H1 « Agencement de la Sée » (le nom, pas la spécialité) ; des H4 utilisés sans H3 dans « À propos » |
| Positionnement | « Trois métiers, une seule finition », « Une seule équipe pour tout l'agencement » : les plafonds tendus ne ressortaient pas comme activité principale |
| Images | 3 photos réelles (JPEG 46–200 Ko) ; 3 tuiles de galerie pointaient vers des fichiers inexistants (404 à chaque visite) |
| Données structurées | `HomeAndConstructionBusiness` valide (adresse, horaires, communes, réseaux sociaux) |
| robots.txt | Correct (tout autorisé + sitemap) |
| Erreurs 404 | Page 404 par défaut de GitHub (en anglais, sans lien vers le site) |
| Performances | Une seule page légère, CSS en ligne ; Turnstile chargé sur toute la page |
| Formulaire | Worker Cloudflare + Turnstile + pot de miel + validation, aucun secret côté navigateur ✔ |

### Ce que je n'ai pas pu vérifier

- **Google Search Console** et la **fiche Google Business Profile** : pas d'accès. Je ne connais ni les positions, ni les impressions, ni les requêtes réelles.
- **Volumes de recherche** : aucun outil de mots-clés n'est connecté. La stratégie ci-dessous repose sur l'intention de recherche et l'observation des résultats Google, pas sur des volumes mesurés.
- **La vidéo TikTok** de référence : bloquée par une connexion et un CAPTCHA.
- **L'envoi réel du formulaire** : testé avec un faux serveur (voir § 5). Je n'ai pas envoyé de vraie demande pour ne pas créer une fausse demande dans votre messagerie.

### Observation des résultats de recherche

- Les recherches locales (« plafond tendu Manche », « Saint-Hilaire », « Vire ») renvoient surtout des **annuaires** (Obat), des **plateformes nationales** avec des pages par ville générées automatiquement, et le **localisateur d'installateurs Barrisol**. Il y a peu de spécialistes locaux avec un vrai contenu : une page métier détaillée a donc une vraie carte à jouer.
- Sur barrisol.com, page « Manche », seuls **2 installateurs** sont listés, dont « LEPROVOST Jérome — Vengeons (50150) », avec votre e-mail mais un lien vers barrisol.fr et sans le nom de l'entreprise. → **Action recommandée** : demander à Barrisol d'afficher « Agencement de la Sée » et le lien `https://agencementdelasee.fr/`. C'est un lien entrant très pertinent et un signal de cohérence (nom, adresse, téléphone).

## 2. Stratégie de mots-clés (hypothèses à valider dans Search Console)

| Page | Intention principale | Formulations ciblées naturellement |
|---|---|---|
| Accueil `/` | Trouver un spécialiste local | plafond tendu Sud Manche / Manche, installateur Barrisol Manche, plafond tendu Sourdeval, nom de l'entreprise |
| Plafonds tendus `/plafonds-tendus-barrisol/` | Comprendre et faire poser | pose de plafond tendu, plafond tendu Barrisol, plafond tendu salle de bains / cuisine, plafond tendu éclairage LED, plafond tendu imprimé, toile translucide verrière, plafond fissuré solution |
| Sols PVC `/sols-pvc/` | Faire poser un sol | pose sol PVC, sol souple salle de bains, sol PVC sur carrelage |
| Menuiseries `/menuiseries-interieures/` | Faire poser portes / placards | pose porte intérieure, placard, menuiserie intérieure Sud Manche |
| Réalisations `/realisations/` | Preuve, inspiration | réalisations plafond tendu, plafond tendu imprimé photo |
| FAQ `/faq/` | Questions précises | combien de temps pour poser un plafond tendu, plafond tendu sur plafond abîmé, entretien plafond tendu |

Chaque page a une fonction distincte : aucune page ne vise les mêmes requêtes qu'une autre. **Aucune page « ville » n'a été créée** : les communes (Sourdeval, Mortain-Bocage, Saint-Hilaire-du-Harcouët, Brécey, Vire Normandie) sont citées naturellement. Une page locale ne serait utile qu'avec du contenu propre (chantiers réels dans la commune, photos).

## 3. Ce qui a été fait

### Architecture (URL → rôle)

| URL | Rôle | Indexée |
|---|---|---|
| `/` | Accueil, centré sur le plafond tendu | oui |
| `/plafonds-tendus-barrisol/` | Page métier prioritaire | oui |
| `/sols-pvc/` | Activité complémentaire | oui |
| `/menuiseries-interieures/` | Activité complémentaire | oui |
| `/realisations/` | Galerie filtrable + visionneuse | oui |
| `/a-propos/` | Entreprise, engagements, zone | oui |
| `/faq/` | 21 questions en 6 catégories | oui |
| `/contact/` | Formulaire de devis + coordonnées | oui |
| `/contact/merci/` | Confirmation après envoi | non |
| `/mentions-legales/`, `/politique-de-confidentialite/` | Pages légales | non (exclues du sitemap) |
| `/404.html` | Page d'erreur avec liens utiles | non |

### Correspondance anciennes → nouvelles adresses

| Ancienne | Nouvelle | Méthode |
|---|---|---|
| `/mentions-legales.html` | `/mentions-legales/` | page de redirection immédiate + canonique |
| `/confidentialite.html` | `/politique-de-confidentialite/` | page de redirection immédiate + canonique |
| `/index.html` | `/` | canonique vers `/` |
| `/#a-propos`, `/#services`, `/#galerie`… | — | les ancres ne sont pas indexées séparément : aucune action nécessaire |

GitHub Pages ne permet pas de vraie redirection 301. La redirection immédiate (`meta refresh` à 0 seconde) est traitée par Google comme une redirection permanente. Comme ces deux pages étaient déjà en `noindex`, le risque SEO est nul.

### SEO technique (sur chaque page)

- Un title et une meta description uniques (moins de 160 caractères), un seul H1, une hiérarchie H2/H3 cohérente.
- Une balise canonique absolue sur les pages indexables, `noindex, follow` sur les autres.
- Balises Open Graph et Twitter, avec une image de partage 1200 × 630 générée à partir d'une photo réelle.
- Données structurées : `HomeAndConstructionBusiness` (reprise des informations existantes) sur l'accueil, À propos, Contact et les pages métiers ; `Service` sur les 3 pages métiers ; `BreadcrumbList` sur les pages internes ; `WebSite` sur l'accueil. Tous les blocs JSON-LD ont été validés comme du JSON correct.
  - Pas de balisage FAQ : depuis 2023, Google n'affiche plus ces résultats enrichis pour ce type de site.
  - Aucun avis, aucune note, aucun prix.
- `sitemap.xml` : les 8 pages canoniques indexables uniquement. `robots.txt` est inchangé (il était correct).
- Maillage interne : les pages métiers renvoient entre elles, vers la galerie filtrée (`/realisations/#plafonds`), vers la FAQ et vers le contact avec la prestation présélectionnée (`/contact/?objet=plafond`). Un fil d'Ariane est présent sur les pages internes.
- Images : conversion en WebP (de 14 à 137 Ko) avec une variante 800 px, dimensions explicites, chargement différé hors écran, préchargement de l'image principale, textes `alt` descriptifs.

### Design

- Les couleurs du logo sont conservées et centralisées (`--rouge #E2001A`, `--bleu #1463C9`, `--sable #DE8F2C`, encre). Les polices existantes sont gardées (Space Grotesk, Work Sans).
- Hero plein écran sur une photo réelle (le plafond imprimé), alternance de sections claires et sombres, cartes de finitions, galerie éditoriale de tailles variées, étapes du projet avec photo fixe, bande d'appel à l'action finale.
- Animations sobres : apparition au défilement, ligne de progression des étapes, léger zoom au survol, accordéons et menus animés. Elles sont toutes désactivées si le visiteur a demandé à réduire les animations.
- Mobile : menu plein écran, bouton d'appel fixe (conservé), formulaire pleine largeur pour le widget Turnstile.
- Le positionnement « 3 métiers » a été supprimé partout. Les sols PVC et la menuiserie sont présentés comme des compléments.

### Photos

- Les 3 photos réelles sont utilisées.
- **11 emplacements** sont prévus pour les photos à venir. La liste à jour, avec noms de fichiers et dimensions, est dans `_src/EMPLACEMENTS-PHOTOS.md`. Ajoutez `?emplacements` à une adresse du site pour les voir encadrés en rouge.
- Aucune photo d'illustration n'est présentée comme une réalisation de l'entreprise.

## 4. Fonctionnalités conservées

- **Formulaire** : même Worker, même clé Turnstile, même pot de miel, mêmes noms de champs et mêmes libellés d'objet, même validation (téléphone, e-mail, longueur), même consentement, même gestion d'erreur avec réinitialisation de Turnstile, et toujours aucun secret dans le code.
  - Ajouts : la prestation est présélectionnée depuis les pages métiers ; après un envoi réussi, le visiteur arrive sur la page de confirmation `/contact/merci/`.
- Turnstile n'est plus chargé que sur `/contact/` (moins de scripts tiers ailleurs). La politique de confidentialité a été mise à jour en conséquence (date : 28 octobre 2026).
- Contenu des mentions légales et de la politique de confidentialité : inchangé, sauf la phrase sur Turnstile.
- `CNAME`, fichier de vérification Google `google5833d2e03f7563c8.html`, favicons, `robots.txt` : intacts.

## 5. Tests effectués

- **Construction et liens** : `python _src/build.py` génère 12 pages et ne trouve aucun lien interne cassé (liens, images, scripts, ancres).
- **Balises** : audit automatique de chaque page (title, description, H1, canonique, JSON-LD, `alt`, sauts de niveaux de titres) sans aucune anomalie ; pas de title en double.
- **Formulaire** (réseau simulé, aucune requête envoyée au Worker) :
  - un envoi vide déclenche 5 erreurs et place le focus sur le premier champ ;
  - sans jeton Turnstile, le message anti-robot s'affiche et rien n'est envoyé ;
  - quand le serveur répond 500, le message d'erreur s'affiche et le bouton est réactivé ;
  - quand le serveur répond 200, le visiteur est redirigé vers `/contact/merci/` ;
  - les données envoyées sont identiques, champ pour champ, à celles de l'ancien site.
- **Menu** : ouverture et fermeture mobile, sous-menu « Nos métiers », fermeture avec Échap, sous-menu masqué au clavier quand il est replié.
- **Galerie** : filtres (3 photos dans « plafonds » ; message « bientôt » dans « sols » et « menuiseries »), visionneuse (ouverture, photo suivante).
- **Emplacements photo** : une photo de test déposée dans `images/photos/` a bien remplacé son emplacement sans reconstruction ; elle a été supprimée ensuite.
- **Responsive** : aucun défilement horizontal sur les 12 pages à 1280 px ; corrections à 320, 360 et 375 px (adresse e-mail trop longue, largeur fixe du widget Turnstile), puis nouvelle vérification.
- **Limite** : je n'ai pas pu faire de revue visuelle complète page par page, car les captures du navigateur intégré échouaient quand la fenêtre était en arrière-plan. L'accueil a été vérifié visuellement sur ordinateur et sur mobile ; le reste l'a été par mesures automatiques. **Une relecture visuelle de votre part reste nécessaire**, surtout sur Safari iOS (pas testé).

## 6. Points à confirmer de votre part

1. **Finitions « satinées » et toiles de couleur** : elles étaient sur l'ancien site, je les ai gardées. Le mat, l'imprimé, le translucide et l'éclairage LED périphérique sont visibles sur vos photos.
2. **Éclairage** : spots encastrés et suspensions sont mentionnés. Les suspensions et le ruban LED sont visibles sur une photo ; confirmez les spots.
3. **Sols PVC** : formats posés (lés, lames, dalles ?), marques, pose sur carrelage existant (formulée prudemment), pièces humides.
4. **Menuiseries** : fournissez-vous le matériel ? Faites-vous de la fabrication ou du sur-mesure ? (Volontairement non promis.)
5. **Horaires** (lundi–vendredi 9h–12h / 14h–18h, samedi sur rendez-vous) et **liste des communes** : repris de l'ancien site, à confirmer. Ils doivent être identiques à ceux de la fiche Google Business Profile.
6. **Adresse** : le site indique « La Gare - Sourdeval » ; Barrisol indique « Vengeons (50150) ». À harmoniser, et à faire corriger chez Barrisol si besoin.
7. **Assurance** : les activités assurées listées dans les mentions légales ne citent pas explicitement les plafonds tendus ni les sols souples. Cela vaut la peine de vérifier avec votre assureur que ces activités sont bien couvertes. Ce n'est pas un avis juridique.
8. **Photos prioritaires** : une grande photo d'accueil (2400 px), un plafond en salon, salle de bains et cuisine, une photo de pose, puis vos sols et menuiseries.
9. **Envoi de photos par le formulaire** : non ajouté, car il faudrait modifier le Worker (taille des fichiers, stockage, filtrage). Pour l'instant, le site invite à envoyer les photos par e-mail.

## 7. Après la mise en ligne

1. Dans Google Search Console :
   - soumettre `https://agencementdelasee.fr/sitemap.xml` ;
   - demander l'indexation de `/plafonds-tendus-barrisol/` ;
   - surveiller le rapport « Pages » (pages indexées ou exclues).
2. Après 4 à 8 semaines, regarder le rapport « Performances » : requêtes, pages, CTR. Ajuster les titles des pages qui ont des impressions mais peu de clics.
3. Compter les demandes : le nombre de visites de `/contact/merci/` correspond au nombre de demandes envoyées. Pour le mesurer, il faudrait un outil d'audience. Je n'en ai pas ajouté : si vous en voulez un, choisissez un outil sans cookie (ex. Plausible ou Cloudflare Web Analytics) ou ajoutez un bandeau de consentement, et mettez à jour la politique de confidentialité.
4. Mettre à jour la fiche Google Business Profile : lien vers le site, catégories, photos.
5. Demander à Barrisol de corriger votre fiche d'installateur (voir § 1).
6. Mesurer les performances avec PageSpeed Insights sur `/` et `/plafonds-tendus-barrisol/`, une fois le site en ligne.
