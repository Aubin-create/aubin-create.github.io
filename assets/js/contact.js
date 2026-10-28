// =========================================================
// FORMULAIRE DE DEMANDE DE DEVIS (page /contact/)
// Envoi : navigateur -> Worker Cloudflare (vérifie Turnstile et les champs)
//         -> Make -> Gmail / Google Sheets.
// Aucune clé ni URL de webhook Make n'est présente côté navigateur.
// =========================================================
const WORKER_URL = 'https://workeragencelentdelasee.v4thbcdt5n.workers.dev/';

const formulaire = document.getElementById('formulaireContact');
const erreurEnvoi = document.getElementById('erreurEnvoi');
const erreurRobot = document.getElementById('erreurRobot');

// Objet présélectionné depuis les pages métiers : /contact/?objet=plafond
const OBJETS = {
  plafond: 'Devis plafond tendu Barrisol',
  sol: 'Devis sol souple PVC',
  menuiserie: 'Devis menuiserie intérieure',
};
const objetDemande = OBJETS[new URLSearchParams(location.search).get('objet')];
if (objetDemande) document.getElementById('sujet').value = objetDemande;

// Date minimale du champ « Période souhaitée » = aujourd'hui
const champDate = document.getElementById('date');
champDate.min = new Date().toISOString().split('T')[0];

function validerChamp(champEl){
  const groupe = champEl.closest('.champ');
  if (!groupe) return true;
  const valide = champEl.checkValidity();
  groupe.classList.toggle('erreur', !valide);
  champEl.setAttribute('aria-invalid', String(!valide));
  return valide;
}

formulaire.querySelectorAll('input, select, textarea').forEach(champEl => {
  champEl.addEventListener('blur', () => validerChamp(champEl));
  champEl.addEventListener('input', () => {
    const groupe = champEl.closest('.champ');
    if (groupe && groupe.classList.contains('erreur')) validerChamp(champEl);
  });
});

formulaire.addEventListener('submit', async (evenement) => {
  evenement.preventDefault();

  // 1. On valide AVANT d'envoyer quoi que ce soit
  let formulaireValide = true;
  formulaire.querySelectorAll('input, select, textarea').forEach(champEl => {
    if (!validerChamp(champEl)) formulaireValide = false;
  });
  if (!formulaireValide){
    const premierChampInvalide = formulaire.querySelector('.champ.erreur input, .champ.erreur select, .champ.erreur textarea');
    if (premierChampInvalide) premierChampInvalide.focus();
    return;
  }

  // 2. Turnstile doit avoir produit son jeton
  const jeton = formulaire.querySelector('[name="cf-turnstile-response"]');
  erreurRobot.hidden = true;
  if (!jeton || !jeton.value){
    erreurRobot.hidden = false;
    return;
  }

  // 3. Envoi
  const bouton = formulaire.querySelector('button[type="submit"]');
  const libelleInitial = bouton.textContent;
  bouton.disabled = true;
  bouton.textContent = 'Envoi en cours…';
  erreurEnvoi.hidden = true;

  try {
    const reponse = await fetch(WORKER_URL, {
      method: 'POST',
      body: new URLSearchParams(new FormData(formulaire))
    });
    if (!reponse.ok) throw new Error('Réponse ' + reponse.status);

    // 4. Succès : page de confirmation (adresse distincte, utile pour le suivi des demandes)
    location.assign('/contact/merci/');
  } catch (erreur) {
    // Un jeton Turnstile ne sert qu'une fois : on en redemande un pour le prochain essai
    if (window.turnstile) window.turnstile.reset();
    bouton.disabled = false;
    bouton.textContent = libelleInitial;
    erreurEnvoi.hidden = false;
  }
});

// Bouton d'appel mobile : masqué pendant la saisie pour ne pas cacher les champs
const appelMobile = document.querySelector('.appel-mobile');
formulaire.addEventListener('focusin', () => appelMobile.classList.add('masque'));
formulaire.addEventListener('focusout', () => appelMobile.classList.remove('masque'));
