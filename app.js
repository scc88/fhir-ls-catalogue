// FHIR-LS Catalogue — app.js
// Minor interactivity for the homepage and catalogue

document.addEventListener('DOMContentLoaded', function () {

  // Animate stats on scroll
  const statNums = document.querySelectorAll('.stat-num');
  if (statNums.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    statNums.forEach(el => observer.observe(el));
  }

  function animateCounter(el) {
    const target = parseFloat(el.textContent);
    const suffix = el.textContent.replace(/[\d.]/g, '');
    const isFloat = el.textContent.includes('.');
    let start = 0;
    const duration = 1200;
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (target - start) * eased;
      el.textContent = (isFloat ? current.toFixed(1) : Math.round(current)) + suffix;
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  // Sticky header shadow on scroll
  const header = document.querySelector('.site-header');
  if (header) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 20) {
        header.style.boxShadow = '0 4px 16px rgba(9,30,66,0.15)';
      } else {
        header.style.boxShadow = '';
      }
    });
  }

  // Lifecycle phase hover
  const phases = document.querySelectorAll('.lifecycle-phase');
  phases.forEach(phase => {
    phase.addEventListener('mouseenter', () => {
      phases.forEach(p => p.style.opacity = '0.4');
      phase.style.opacity = '1';
    });
    phase.addEventListener('mouseleave', () => {
      phases.forEach(p => p.style.opacity = '1');
    });
  });

  // Standard card entrance animation
  const cards = document.querySelectorAll('.standard-card');
  if (cards.length) {
    const cardObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
          }, i * 80);
          cardObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    cards.forEach(card => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(20px)';
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease, box-shadow 0.2s, border-color 0.2s';
      cardObserver.observe(card);
    });
  }

});
