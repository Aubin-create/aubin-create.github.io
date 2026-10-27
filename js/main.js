// =========================================================
// NAVIGATION MOBILE (menu hamburger)
// =========================================================
const navBascule = document.getElementById('navBascule');
const navLiens = document.getElementById('navLiens');

navBascule.addEventListener('click', () => {
  const ouvert = navBascule.getAttribute('aria-expanded') === 'true';
  navBascule.setAttribute('aria-expanded', String(!ouvert));
  navLiens.classList.toggle('ouvert');
});

navLiens.querySelectorAll('a').forEach(lien => {
  lien.addEventListener('click', () => {
    navBascule.setAttribute('aria-expanded', 'false');
    navLiens.classList.remove('ouvert');
  });
});

// =========================================================
// RÉVÉLATION AU SCROLL (fade-in léger)
// =========================================================
const elementsReveles = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window){
  const observateur = new IntersectionObserver((entrees) => {
    entrees.forEach(entree => {
      if (entree.isIntersecting){
        entree.target.classList.add('visible');
        observateur.unobserve(entree.target);
      }
    });
  }, { threshold: 0.05, rootMargin: '0px 0px -40px 0px' });

  elementsReveles.forEach(el => observateur.observe(el));
} else {
  elementsReveles.forEach(el => el.classList.add('visible'));
}

// =========================================================
// ANNÉE COURANTE DANS LE PIED DE PAGE
// =========================================================
document.getElementById('anneeCourante').textContent = new Date().getFullYear();
