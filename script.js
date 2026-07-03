(function () {
  const header = document.querySelector('.site-header');
  const navLinks = document.querySelector('.nav-main');
  const menuToggle = document.querySelector('.menu-toggle');
  const navAnchors = document.querySelectorAll('.nav-main a');
  const sections = [...navAnchors]
    .map((a) => document.getElementById(a.getAttribute('href').slice(1)))
    .filter(Boolean);

  window.addEventListener('scroll', () => {
    header.classList.toggle('scrolled', window.scrollY > 8);
  });

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', open);
    });

    navLinks.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const id = entry.target.id;
        navAnchors.forEach((a) => {
          a.classList.toggle('active', a.getAttribute('href') === '#' + id);
        });
      });
    },
    { rootMargin: '-40% 0px -50% 0px', threshold: 0 }
  );

  sections.forEach((section) => {
    if (section.id) observer.observe(section);
  });

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  document.querySelectorAll('.btn-grad, .btn-white').forEach((btn) => {
    if (btn.textContent.trim() === 'Learn More') {
      btn.addEventListener('click', () => {
        document.querySelector('#contact')?.scrollIntoView({ behavior: 'smooth' });
      });
    }
  });
})();
