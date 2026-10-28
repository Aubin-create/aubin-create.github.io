// =========================================================
// Agencement de la Sée — scripts communes à toutes les pages
// =========================================================

// ---------- En-tête : ombre au défilement ----------
const entete = document.getElementById('entete');
const majEntete = () => entete.classList.toggle('defile', window.scrollY > 8);
majEntete();
window.addEventListener('scroll', majEntete, { passive: true });

// ---------- Menu mobile ----------
const navBascule = document.getElementById('navBascule');
const navPrincipale = document.getElementById('navPrincipale');

function fermerMenu(){
  navBascule.setAttribute('aria-expanded', 'false');
  navPrincipale.classList.remove('ouvert');
  document.body.classList.remove('menu-ouvert');
}

navBascule.addEventListener('click', () => {
  const ouvert = navBascule.getAttribute('aria-expanded') === 'true';
  if (ouvert) return fermerMenu();
  navBascule.setAttribute('aria-expanded', 'true');
  navPrincipale.classList.add('ouvert');
  document.body.classList.add('menu-ouvert');
});

// ---------- Menu déroulant « Nos métiers » ----------
const deroulant = document.querySelector('.nav-deroulant');
const boutonDeroulant = deroulant.querySelector('.nav-deroulant-bouton');
const bureau = window.matchMedia('(min-width: 1080px)');

function basculerSousMenu(ouvrir){
  boutonDeroulant.setAttribute('aria-expanded', String(ouvrir));
}
boutonDeroulant.addEventListener('click', () => {
  basculerSousMenu(boutonDeroulant.getAttribute('aria-expanded') !== 'true');
});
deroulant.addEventListener('mouseenter', () => { if (bureau.matches) basculerSousMenu(true); });
deroulant.addEventListener('mouseleave', () => { if (bureau.matches) basculerSousMenu(false); });
deroulant.addEventListener('focusout', (e) => {
  if (bureau.matches && !deroulant.contains(e.relatedTarget)) basculerSousMenu(false);
});

document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (boutonDeroulant.getAttribute('aria-expanded') === 'true'){
    basculerSousMenu(false);
    boutonDeroulant.focus();
  } else if (navBascule.getAttribute('aria-expanded') === 'true'){
    fermerMenu();
    navBascule.focus();
  }
});
document.addEventListener('click', (e) => {
  if (bureau.matches && !deroulant.contains(e.target)) basculerSousMenu(false);
});
bureau.addEventListener('change', () => { fermerMenu(); basculerSousMenu(false); });

// ---------- Révélation au défilement ----------
const aReveler = document.querySelectorAll('.reveal, .etapes');
if ('IntersectionObserver' in window){
  const observateur = new IntersectionObserver((entrees) => {
    entrees.forEach(entree => {
      if (entree.isIntersecting){
        entree.target.classList.add('visible');
        observateur.unobserve(entree.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  aReveler.forEach(el => observateur.observe(el));
} else {
  aReveler.forEach(el => el.classList.add('visible'));
}

// ---------- Emplacements photo ----------
// Si une photo attendue a été déposée dans images/photos/ sans relancer la
// construction du site, on l'affiche à la place de l'emplacement « Photo à venir ».
// La vérification n'a lieu que lorsque l'emplacement approche de l'écran.
function sonderPhoto(zone){
  const img = new Image();
  img.onload = () => {
    img.alt = zone.dataset.alt;
    img.width = img.naturalWidth;
    img.height = img.naturalHeight;
    img.decoding = 'async';
    zone.replaceWith(img);
    const item = img.closest('.galerie-item');
    if (item) item.classList.remove('est-vide');
    const figure = img.closest('.photo--vide');
    if (figure) figure.classList.remove('photo--vide');
    document.dispatchEvent(new CustomEvent('photo-ajoutee'));
  };
  img.src = '/images/photos/' + zone.dataset.photo + '.webp';
}
const zonesPhoto = document.querySelectorAll('.photo-attente[data-photo]');
if ('IntersectionObserver' in window){
  const sonde = new IntersectionObserver((entrees) => {
    entrees.forEach(entree => {
      if (!entree.isIntersecting) return;
      sonde.unobserve(entree.target);
      sonderPhoto(entree.target);
    });
  }, { rootMargin: '300px 0px' });
  // Les vignettes masquées de la galerie ne deviennent jamais visibles : on les vérifie tout de suite.
  zonesPhoto.forEach(zone => zone.closest('.est-vide') ? sonderPhoto(zone) : sonde.observe(zone));
} else {
  zonesPhoto.forEach(sonderPhoto);
}

// Mode « ?emplacements » : encadre les photos à fournir (mémorisé pour la session)
try {
  const params = new URLSearchParams(location.search);
  if (params.has('emplacements')) sessionStorage.setItem('emplacements', '1');
  if (params.has('sans-emplacements')) sessionStorage.removeItem('emplacements');
  if (sessionStorage.getItem('emplacements')){
    document.documentElement.classList.add('mode-emplacements');
    const nb = document.querySelectorAll('.photo-attente[data-photo]').length;
    const bandeau = document.createElement('div');
    bandeau.className = 'bandeau-emplacements';
    bandeau.innerHTML = '<strong>Mode emplacements photo</strong><br>' + nb +
      ' emplacement(s) à compléter sur cette page. Nom du fichier et dimensions indiqués dans chaque cadre.' +
      '<br><button type="button">Quitter ce mode</button>';
    bandeau.querySelector('button').addEventListener('click', () => {
      sessionStorage.removeItem('emplacements');
      location.href = location.pathname;
    });
    document.body.appendChild(bandeau);
  }
} catch (e) { /* stockage indisponible : mode ignoré */ }

// ---------- Galerie : filtres + visionneuse ----------
const galerie = document.getElementById('galerie');
if (galerie){
  const filtres = document.querySelectorAll('.filtre');
  const messageVide = document.getElementById('galerieVide');
  let filtreActif = 'tous';

  function appliquerFiltre(){
    let visibles = 0;
    galerie.querySelectorAll('.galerie-item').forEach(item => {
      const masque = filtreActif !== 'tous' && item.dataset.cat !== filtreActif;
      item.classList.toggle('filtre-masque', masque);
      if (!masque && !item.classList.contains('est-vide')) visibles++;
    });
    messageVide.hidden = visibles > 0;
  }

  filtres.forEach(bouton => bouton.addEventListener('click', () => {
    filtres.forEach(b => b.setAttribute('aria-pressed', String(b === bouton)));
    filtreActif = bouton.dataset.filtre;
    appliquerFiltre();
  }));
  // Filtre direct depuis une page métier : /realisations/#plafonds
  const depuisAncre = location.hash.slice(1);
  const boutonAncre = [...filtres].find(b => b.dataset.filtre === depuisAncre);
  if (boutonAncre) boutonAncre.click();
  document.addEventListener('photo-ajoutee', appliquerFiltre);

  // Visionneuse
  const visionneuse = document.createElement('dialog');
  visionneuse.className = 'visionneuse';
  visionneuse.setAttribute('aria-label', 'Photo agrandie');
  visionneuse.innerHTML =
    '<figure><img alt=""><figcaption></figcaption></figure>' +
    '<button type="button" class="visionneuse-bouton visionneuse-fermer" aria-label="Fermer">✕</button>' +
    '<button type="button" class="visionneuse-bouton visionneuse-prec" aria-label="Photo précédente">←</button>' +
    '<button type="button" class="visionneuse-bouton visionneuse-suiv" aria-label="Photo suivante">→</button>';
  document.body.appendChild(visionneuse);
  const imgGrande = visionneuse.querySelector('img');
  const legende = visionneuse.querySelector('figcaption');
  let courant = 0;

  const ouvrables = () => [...galerie.querySelectorAll('.galerie-item:not(.est-vide):not(.filtre-masque) .galerie-ouvrir')]
    .filter(b => b.querySelector('img'));

  function montrer(index){
    const liste = ouvrables();
    if (!liste.length) return;
    courant = (index + liste.length) % liste.length;
    const bouton = liste[courant];
    const img = bouton.querySelector('img');
    imgGrande.src = img.currentSrc || img.src;
    imgGrande.alt = img.alt;
    const fig = bouton.closest('figure').querySelector('figcaption');
    legende.innerHTML = fig ? fig.innerHTML : '';
  }

  galerie.addEventListener('click', (e) => {
    const bouton = e.target.closest('.galerie-ouvrir');
    if (!bouton || !bouton.querySelector('img')) return;
    montrer(ouvrables().indexOf(bouton));
    visionneuse.showModal();
  });
  visionneuse.querySelector('.visionneuse-fermer').addEventListener('click', () => visionneuse.close());
  visionneuse.querySelector('.visionneuse-prec').addEventListener('click', () => montrer(courant - 1));
  visionneuse.querySelector('.visionneuse-suiv').addEventListener('click', () => montrer(courant + 1));
  visionneuse.addEventListener('click', (e) => { if (e.target === visionneuse) visionneuse.close(); });
  visionneuse.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') montrer(courant - 1);
    if (e.key === 'ArrowRight') montrer(courant + 1);
  });
}
