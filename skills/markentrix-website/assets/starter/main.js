// Progressive Enhancement: Seite funktioniert auch ohne dieses Skript.
document.documentElement.classList.add('js');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const targets = document.querySelectorAll('[data-reveal], .curve');
if (reduce || !('IntersectionObserver' in window)) {
  targets.forEach(el => el.classList.add('is-in'));
} else {
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
  targets.forEach(el => io.observe(el));
}
