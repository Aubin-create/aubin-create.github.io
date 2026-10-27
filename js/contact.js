// =========================================================
// DATE MINIMALE DU CHAMP "DATE SOUHAITÉE" = AUJOURD'HUI
// =========================================================
const champDate = document.getElementById('date');
if (champDate){
  const aujourdHui = new Date().toISOString().split('T')[0];
  champDate.min = aujourdHui;
}

// =========================================================
// VALIDATION ET ENVOI DU FORMULAIRE DE CONTACT
// =========================================================
const formulaire = document.getElementById('formulaireContact');
const confirmation = document.getElementById('confirmationEnvoi');
const erreurEnvoi = document.getElementById('erreurEnvoi');

function validerChamp(champEl){
  const groupe = champEl.closest('.champ');
  if (!groupe) return true;
  const valide = champEl.checkValidity();
  groupe.classList.toggle('erreur', !valide);
  return valide;
}

formulaire.querySelectorAll('input, select, textarea').forEach(champEl => {
  champEl.addEventListener('blur', () => validerChamp(champEl));
  champEl.addEventListener('input', () => {
    const groupe = champEl.closest('.champ');
    if (groupe && groupe.classList.contains('erreur')) validerChamp(champEl);
  });
});

// Le formulaire n'envoie plus directement à Make : il passe par le Worker Cloudflare,
// qui vérifie Turnstile et les champs avant de transmettre à Make.
const WORKER_URL = 'https://workeragencelentdelasee.v4thbcdt5n.workers.dev/';
const erreurRobot = document.getElementById('erreurRobot');

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
  bouton.textContent = 'Envoi…';
  erreurEnvoi.hidden = true;

  try {
    const reponse = await fetch(WORKER_URL, {
      method: 'POST',
      body: new URLSearchParams(new FormData(formulaire))
    });
    if (!reponse.ok) throw new Error('Réponse ' + reponse.status);

    // 4. Succès : on masque le formulaire et on affiche la confirmation
    formulaire.style.display = 'none';
    confirmation.classList.add('visible');
    confirmation.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } catch (erreur) {
    // Un jeton Turnstile ne sert qu'une fois : on en redemande un pour le prochain essai
    if (window.turnstile) window.turnstile.reset();
    bouton.disabled = false;
    bouton.textContent = libelleInitial;
    erreurEnvoi.hidden = false;
  }
});

// =========================================================
// BOUTON D'APPEL MOBILE : masqué pendant la saisie pour ne pas cacher les champs
// =========================================================
const appelMobile = document.querySelector('.appel-mobile');
formulaire.addEventListener('focusin', () => appelMobile.classList.add('masque'));
formulaire.addEventListener('focusout', () => appelMobile.classList.remove('masque'));
