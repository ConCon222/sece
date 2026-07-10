document.addEventListener("DOMContentLoaded", function () {
  "use strict";

  document.querySelectorAll("[data-context-rail]").forEach(function (rail) {
    var links = Array.from(rail.querySelectorAll("a[data-section]"));
    var sections = links
      .map(function (link) {
        var section = document.getElementById(link.dataset.section);
        return section ? { link: link, section: section } : null;
      })
      .filter(Boolean);
    var ticking = false;

    if (!sections.length) return;

    function update() {
      var marker = window.scrollY + window.innerHeight * 0.28;
      var current = sections[0];

      sections.forEach(function (item) {
        var top = item.section.getBoundingClientRect().top + window.scrollY;
        if (top <= marker) current = item;
      });

      links.forEach(function (link) {
        var active = link === current.link;
        link.classList.toggle("active", active);
        if (active) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
      ticking = false;
    }

    function requestUpdate() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    }

    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestUpdate);
    window.addEventListener("load", requestUpdate);
    window.addEventListener("hashchange", requestUpdate);
    window.addEventListener(
      "context-rail:ready",
      function () {
        var target = window.location.hash ? document.getElementById(decodeURIComponent(window.location.hash.slice(1))) : null;
        if (target) target.scrollIntoView({ block: "start" });
        requestUpdate();
      },
      { once: true }
    );
    rail.addEventListener("click", function (event) {
      var link = event.target.closest("a[data-section]");
      if (!link) return;
      links.forEach(function (item) {
        item.classList.toggle("active", item === link);
      });
    });
    update();
  });
});
