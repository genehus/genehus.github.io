(function () {
  const header = document.querySelector('.site-header');
  const nav = document.querySelector('.nav-main');
  const menuToggle = document.querySelector('.menu-toggle');
  const navAnchors = document.querySelectorAll('.nav-main a');

  const onScroll = () => {
    header?.classList.toggle('is-scrolled', window.scrollY > 24);
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      header?.classList.toggle('is-open', open);
      menuToggle.setAttribute('aria-expanded', String(open));
    });

    nav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        nav.classList.remove('open');
        header?.classList.remove('is-open');
        menuToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  const sectionIds = [...navAnchors]
    .map((a) => a.getAttribute('href'))
    .filter((href) => href && href.startsWith('#'))
    .map((href) => document.querySelector(href))
    .filter(Boolean);

  if (sectionIds.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const id = '#' + entry.target.id;
          navAnchors.forEach((a) => {
            a.classList.toggle('active', a.getAttribute('href') === id);
          });
        });
      },
      { rootMargin: '-35% 0px -55% 0px', threshold: 0 }
    );
    sectionIds.forEach((el) => observer.observe(el));
  }

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const href = anchor.getAttribute('href');
      if (!href || href === '#') return;
      const target = document.querySelector(href);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  const revealEls = document.querySelectorAll(
    '.platform, .problem, .process, .technology, .paths, .partners, .pipeline, .about, .team, .contact, .intro, .interest, .indications'
  );
  revealEls.forEach((el) => el.classList.add('reveal'));

  const brand = document.querySelector('.about-brand');
  const aboutSection = document.querySelector('#about');

  const playBrandAnimation = () => {
    if (!brand || brand.classList.contains('is-animated')) return;
    brand.classList.add('is-animated');
  };

  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          if (entry.target.id === 'about' || (brand && entry.target.contains(brand))) {
            playBrandAnimation();
          }
          revealObserver.unobserve(entry.target);
        });
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.12 }
    );
    revealEls.forEach((el) => revealObserver.observe(el));

    if (brand) {
      const brandObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            playBrandAnimation();
            brandObserver.unobserve(brand);
          });
        },
        { rootMargin: '0px 0px -5% 0px', threshold: 0.2 }
      );
      brandObserver.observe(brand);
    }

    if (aboutSection) {
      const aboutObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            playBrandAnimation();
            aboutObserver.unobserve(aboutSection);
          });
        },
        { threshold: 0.15 }
      );
      aboutObserver.observe(aboutSection);
    }
  } else {
    revealEls.forEach((el) => el.classList.add('is-visible'));
    playBrandAnimation();
  }

  // Fallback so the panel never stays empty if observers miss
  window.setTimeout(playBrandAnimation, 1800);

  const newsletterInput = document.querySelector('#newsletter-email');
  const newsletterSubmit = document.querySelector('.newsletter-submit');

  if (newsletterInput && newsletterSubmit) {
    const subscribe = () => {
      const email = newsletterInput.value.trim();
      if (!newsletterInput.checkValidity() || !email) {
        newsletterInput.focus();
        return;
      }
      const subject = encodeURIComponent('Newsletter subscription');
      const body = encodeURIComponent(`Please add ${email} to the GeneHus newsletter.`);
      window.location.href = `mailto:info@genehus.bio?subject=${subject}&body=${body}`;
      newsletterInput.value = '';
    };

    newsletterSubmit.addEventListener('click', subscribe);
    newsletterInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') subscribe();
    });
  }

  const form = document.querySelector('#contact-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const data = new FormData(form);
      const lines = [...data.entries()]
        .map(([key, value]) => `${key}: ${value}`)
        .join('\n');
      const subject = encodeURIComponent('GeneHus website inquiry');
      const body = encodeURIComponent(lines);
      window.location.href = `mailto:partnerships@genehus.bio?subject=${subject}&body=${body}`;
    });
  }
})();
