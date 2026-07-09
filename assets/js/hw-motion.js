/* ============================================================
   hw-motion.js — elegant, self-hosted GSAP motion layer.
   SCOPE: only the home/About page (.hw-home) and the Life Line page
   (.lifeline) get motion. Data/utility pages stay still.

   Activated only when <html> has class "hw-anim" (added pre-paint in
   head.liquid, ONLY when prefers-reduced-motion is not set). Pre-hide
   states live in _sass/_purple-glass.scss under html.hw-anim.

   Principles: calm + cohesive. Short durations, gentle power-eases,
   small offsets, plays once, transform/opacity only (compositor), and
   clearProps so the site's CSS hover transforms keep working.
   ============================================================ */
(function () {
  "use strict";
  var root = document.documentElement;
  if (window.__hwAnimFallback) { clearTimeout(window.__hwAnimFallback); window.__hwAnimFallback = null; }

  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
    root.classList.remove("hw-anim");
    return;
  }

  function one(s, c) { return (c || document).querySelector(s); }
  function $(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }

  var isHome = !!one(".hw-home .hero");
  var isLife = !!one(".lifeline");
  if (!isHome && !isLife) { root.classList.remove("hw-anim"); return; } // other pages: no motion, reveal everything

  root.classList.add("hw-anim");
  gsap.registerPlugin(ScrollTrigger);
  gsap.config({ nullTargetWarn: false });
  ScrollTrigger.config({ ignoreMobileResize: true });
  gsap.defaults({ ease: "power3.out", duration: 0.6 });
  var CLEAR = "transform,opacity"; // never clear visibility (CSS pre-hide uses it)

  function prepCount(el) {
    if (!el || el.hasAttribute("data-hw-count")) return;
    var n = parseInt((el.textContent || "").replace(/[,\s]/g, ""), 10);
    if (isNaN(n)) return;
    el.setAttribute("data-hw-count", n);
    el.textContent = "0";
  }
  function runCount(el) {
    if (!el || !el.hasAttribute("data-hw-count")) return;
    var target = parseInt(el.getAttribute("data-hw-count"), 10), o = { v: 0 };
    gsap.to(o, { v: target, duration: 1.1, ease: "power2.out",
      onUpdate: function () { el.textContent = Math.round(o.v).toLocaleString("en-US"); } });
  }
  function batchReveal(selector, opts) {
    opts = opts || {};
    var items = $(selector);
    if (!items.length) return;
    ScrollTrigger.batch(items, {
      start: opts.start || "top 88%", once: true,
      onEnter: function (b) {
        gsap.from(b, { y: opts.y != null ? opts.y : 20, x: opts.x || 0, autoAlpha: 0,
          duration: opts.duration || 0.6, ease: opts.ease || "power3.out",
          stagger: opts.stagger != null ? opts.stagger : 0.08, overwrite: true, clearProps: CLEAR });
      }
    });
  }
  function fadeIn(selector, opts) {
    opts = opts || {};
    $(selector).forEach(function (el) {
      gsap.from(el, { y: opts.y != null ? opts.y : 16, autoAlpha: 0,
        duration: opts.duration || 0.6, ease: "power3.out", clearProps: CLEAR,
        scrollTrigger: { trigger: el, start: opts.start || "top 90%", once: true } });
    });
  }

  /* ================= HOME / ABOUT ================= */
  if (isHome) {
    $(".hw-home .stat-num").forEach(prepCount);

    var tl = gsap.timeline({ delay: 0.06, defaults: { duration: 0.6, ease: "power3.out", clearProps: CLEAR } });
    tl.from(".hw-home .hero-portrait .portrait-frame", { autoAlpha: 0, scale: 0.965, duration: 0.85 }, 0)
      .from(".hw-home .display .line", { y: 24, autoAlpha: 0, stagger: 0.08 }, 0.08)
      .from(".hw-home .tagline", { y: 16, autoAlpha: 0 }, "-=0.30")
      .from(".hw-home .affiliation", { y: 16, autoAlpha: 0 }, "-=0.36")
      // counts WHILE the stat cards fade in (onStart) — no "0 holds then counts" pause
      .from(".hw-home .stats .stat", { y: 14, autoAlpha: 0, stagger: 0.06,
        onStart: function () { $(".hw-home .stat-num").forEach(runCount); } }, "-=0.30")
      .from(".hw-home .badge-floating", { autoAlpha: 0, scale: 0.85, duration: 0.5, ease: "power2.out" }, "-=0.55");

    $(".hw-home .section-head").forEach(function (head) {
      var t = gsap.timeline({ defaults: { ease: "power3.out", clearProps: CLEAR },
        scrollTrigger: { trigger: head, start: "top 88%", once: true } });
      var bits = head.querySelectorAll(".section-num, .section-title, .section-link");
      if (bits.length) t.from(bits, { y: 16, autoAlpha: 0, stagger: 0.05, duration: 0.55 });
      var rule = head.querySelector(".section-rule");
      if (rule) t.from(rule, { scaleX: 0, autoAlpha: 0, transformOrigin: "left center", duration: 0.6, ease: "power2.out" }, "-=0.35");
    });

    fadeIn(".hw-home .about-prose", { y: 22, start: "top 84%" });
    batchReveal(".hw-home .about-side .side-card", { y: 20, stagger: 0.1, start: "top 86%" });
    batchReveal(".hw-home .research-grid .r-card", { y: 22, stagger: 0.08, start: "top 86%" });
    batchReveal(".hw-home .pubs .pub", { y: 20, stagger: 0.1, start: "top 86%" });
    batchReveal(".hw-home .visit-rail .visit-card", { y: 18, stagger: 0.07, start: "top 88%" });

    if (one(".hw-home .contact-card")) {
      var ct = gsap.timeline({ defaults: { ease: "power3.out", clearProps: CLEAR },
        scrollTrigger: { trigger: ".hw-home .contact-card", start: "top 84%", once: true } });
      var eye = one(".hw-home .contact-eyebrow"); if (eye) ct.from(eye, { y: 14, autoAlpha: 0, duration: 0.5 });
      var hd = one(".hw-home .contact-headline"); if (hd) ct.from(hd, { y: 20, autoAlpha: 0, duration: 0.6 }, "-=0.2");
      var its = $(".hw-home .contact-item"); if (its.length) ct.from(its, { y: 16, autoAlpha: 0, stagger: 0.06, duration: 0.5 }, "-=0.25");
    }
  }

  /* ================= LIFE LINE ================= */
  if (isLife) {
    fadeIn(".lifeline-header", { y: 16, start: "top 90%" });
    $(".year-marker").forEach(function (m) {
      gsap.from(m, { scale: 0.85, autoAlpha: 0, duration: 0.5, ease: "power2.out", clearProps: CLEAR,
        scrollTrigger: { trigger: m, start: "top 90%", once: true } });
    });
    $(".event-card").forEach(function (card) {
      gsap.from(card, { x: card.classList.contains("left") ? -32 : 32, autoAlpha: 0, duration: 0.55, ease: "power3.out", clearProps: CLEAR,
        scrollTrigger: { trigger: card, start: "top 90%", once: true } });
    });
    var endDot = one(".lifeline-end-dot");
    if (endDot) gsap.from(endDot, { scale: 0.4, autoAlpha: 0, duration: 0.45, ease: "power2.out", clearProps: CLEAR,
      scrollTrigger: { trigger: endDot, start: "top 94%", once: true } });

    // The Life Line collapses years via max-height (it reserves full height for
    // every card at load). Cards reveal individually on scroll, so a year's lower
    // cards can still be hidden when you toggle it → the re-opened container shows
    // blank space. So: the moment the user interacts with the timeline, FINALIZE —
    // reveal every remaining card at once and kill the scroll-reveals. No
    // ScrollTrigger.refresh (which would cause the "hitch"); runs in capture phase
    // so it happens before toggleYear() measures scrollHeight.
    var finalized = false;
    function finalizeLifeline() {
      if (finalized) return;
      finalized = true;
      var els = $(".lifeline-header, .lifeline .year-marker, .lifeline .event-card, .lifeline-end-dot");
      gsap.set(els, { clearProps: "transform" }); // drop x / scale / y offsets
      els.forEach(function (el) { el.style.opacity = "1"; el.style.visibility = "visible"; }); // beat the CSS pre-hide
      ScrollTrigger.getAll().forEach(function (st) { st.kill(); }); // only lifeline triggers exist on this page
    }
    var llRoot = one(".lifeline");
    if (llRoot) llRoot.addEventListener("click", finalizeLifeline, true);
    var bar = one(".lifeline-toolbar");
    if (bar) bar.addEventListener("click", finalizeLifeline, true);
  }

  window.addEventListener("load", function () { ScrollTrigger.refresh(); });
})();
