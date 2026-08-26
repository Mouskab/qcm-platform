// static/js/main.js

document.addEventListener("DOMContentLoaded", () => {

  // --- Animation de la carte "copie d'examen" dans le hero ---
  const options = document.querySelectorAll(".exam-option");
  const stamp = document.querySelector(".exam-stamp");

  if (options.length && stamp) {
    const cocherOption = () => {
      options.forEach(o => o.classList.remove("is-checked"));
      stamp.classList.remove("is-visible");

      const correcte = options[1]; // la 2e option est notre "bonne réponse" de démo
      setTimeout(() => {
        correcte.classList.add("is-checked");
        setTimeout(() => stamp.classList.add("is-visible"), 350);
      }, 500);
    };
    cocherOption();
    setInterval(cocherOption, 4200);
  }

  // --- Toggle mensuel / trimestriel / annuel (tarifs) ---
  const toggleButtons = document.querySelectorAll(".pricing-toggle button");
  const prixElements = document.querySelectorAll("[data-prix]");

  toggleButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      toggleButtons.forEach(b => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      const duree = btn.dataset.duree;

      prixElements.forEach(el => {
        const valeur = el.dataset[duree];
        if (valeur) el.textContent = valeur;
      });
    });
  });

  // --- Navigation mobile ---
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      navLinks.classList.toggle("is-open");
    });
  }

  // --- Menu utilisateur (dropdown) ---
  const menuTrigger = document.getElementById("user-menu-trigger");
  const menuDropdown = document.getElementById("user-menu-dropdown");

  if (menuTrigger && menuDropdown) {
    menuTrigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const estOuvert = menuDropdown.classList.toggle("is-open");
      menuTrigger.setAttribute("aria-expanded", estOuvert);
    });

    document.addEventListener("click", (e) => {
      if (!menuDropdown.contains(e.target) && !menuTrigger.contains(e.target)) {
        menuDropdown.classList.remove("is-open");
        menuTrigger.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        menuDropdown.classList.remove("is-open");
        menuTrigger.setAttribute("aria-expanded", "false");
      }
    });
  }

});