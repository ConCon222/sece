---
layout: page
title: Life Line
title_zh: 人生轨迹
permalink: /lifeline/
description: ""
nav: true
nav_zh: 人生轨迹
nav_order: 6
---

<!-- This page uses a custom header; suppress the auto-generated page title/description -->
<style>.post-title, .post-description { display: none; }</style>

<!-- ==================== Main Styles ==================== -->
<style>

/* ---------- Timeline Container ---------- */
.lifeline {
  position: relative;
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 0;
}

/* ---------- Center Vertical Line ---------- */
.lifeline::before {
  content: '';
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 100%;
  background: linear-gradient(180deg, transparent, var(--tsinghua-pale, #d9bee0) 8%, var(--tsinghua-pale, #d9bee0) 92%, transparent);
}

/* ---------- Top Header ---------- */
.lifeline-header {
  text-align: center;
  margin-bottom: 2rem;
}

.lifeline-hint {
  color: #94a3b8;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

/* ---------- Toolbar (filters + expand controls, one row) ---------- */
.lifeline-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.toolbar-divider {
  width: 1px;
  height: 1.15rem;
  background: var(--rule, rgba(31,20,41,0.12));
  margin: 0 0.3rem;
}

.filter-pill {
  padding: 0.375rem 0.875rem;
  font-size: 0.75rem;
  font-weight: 500;
  font-family: var(--ui, sans-serif);
  background: rgba(255,255,255,0.6);
  color: var(--ink-soft, #475569);
  border: 1px solid var(--tsinghua-pale, #e2e8f0);
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.filter-pill:hover {
  background: #e2e8f0;
  transform: translateY(-1px);
}

.filter-pill.active {
  color: white;
  border-color: transparent;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.filter-pill.active[data-type="all"]         { background: var(--tsinghua, #660874); }
.filter-pill.active[data-type="award"]       { background: #f59e0b; }
.filter-pill.active[data-type="honor"]       { background: #a855f7; }
.filter-pill.active[data-type="talk"]        { background: #ef4444; }
.filter-pill.active[data-type="project"]     { background: #06b6d4; }
.filter-pill.active[data-type="service"]     { background: #8b5cf6; }
.filter-pill.active[data-type="publication"] { background: #3b82f6; }
.filter-pill.active[data-type="exchange"]    { background: #ec4899; }

/* ---------- Collapsible "By type" toggle ---------- */
.filter-toggle {
  padding: 0.375rem 0.875rem;
  font-size: 0.75rem;
  font-weight: 500;
  font-family: var(--ui, sans-serif);
  background: var(--tsinghua-wash, #f1e6f5);
  color: var(--tsinghua, #660874);
  border: 1px solid var(--tsinghua-pale, #d9bee0);
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  white-space: nowrap;
}
.filter-toggle:hover {
  background: var(--tsinghua, #660874);
  color: #fff;
  border-color: var(--tsinghua, #660874);
  transform: translateY(-1px);
}
.filter-chev {
  font-size: 0.7rem;
  transition: transform 0.3s ease;
  display: inline-block;
}
.filter-toggle.open .filter-chev { transform: rotate(180deg); }

.filter-pills-extra {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  margin-top: 0;
  transition: max-height 0.35s ease, opacity 0.3s ease, margin-top 0.3s ease;
}
.filter-pills-extra.open {
  max-height: 240px;
  opacity: 1;
  margin-top: 0.5rem;
  overflow: visible; /* so the hover lift on pills isn't clipped by the panel edge */
}

.filter-count {
  font-size: 0.65rem;
  opacity: 0.8;
  background: rgba(255,255,255,0.2);
  padding: 0.1rem 0.4rem;
  border-radius: 9999px;
}

.filter-pill:not(.active) .filter-count {
  background: rgba(0,0,0,0.08);
}

/* ---------- Expand / Collapse Buttons ---------- */
.lifeline-controls {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
}

.lifeline-btn {
  padding: 0.375rem 1rem;
  font-size: 0.75rem;
  font-family: var(--ui, sans-serif);
  background: rgba(255,255,255,0.6);
  color: var(--ink-soft, #475569);
  border: 1px solid var(--tsinghua-pale, #e2e8f0);
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s;
}

.lifeline-btn:hover {
  background: var(--tsinghua-wash, #e2e8f0);
  color: var(--tsinghua, #660874);
}

/* ---------- Year Section ---------- */
.year-section {
  position: relative;
  margin-bottom: 1rem;
}

.year-section.hidden-by-filter {
  display: none;
}

/* ---------- Year Marker (clickable) ---------- */
.year-marker {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  z-index: 10;
  margin: 1.5rem 0;
  cursor: pointer;
}

.year-label {
  background: linear-gradient(180deg, var(--tsinghua, #660874), var(--tsinghua-deep, #4a0a5e));
  color: white;
  font-family: var(--display, Georgia, serif);
  font-size: 1.35rem;
  font-weight: 600;
  padding: 0.625rem 1.5rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.year-label:hover {
  background: var(--tsinghua-light, #475569);
  transform: scale(1.05);
}

.year-count {
  background: rgba(255,255,255,0.22);
  color: white;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.year-chevron {
  font-size: 0.875rem;
  color: #94a3b8;
}

/* ---------- Events Container (collapse animation) ---------- */
.events-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow: hidden;
  transition: max-height 0.4s ease;
}
/* Stagger: pull each card up into the previous one's vertical space so
   left/right cards interleave (zigzag) instead of stacking on one line. */
.events-container .event-card + .event-card {
  margin-top: -2.2rem;
}
/* When filtered to one type: (1) hidden cards break the negative-margin
   adjacency → disable the stagger; (2) the JS-set max-height (for the
   collapse animation) becomes stale and clips the now-shorter content →
   release it so cards always show in full. */
.lifeline.filtered .events-container {
  gap: 0.6rem;
  max-height: none !important;
  overflow: visible;
}
.lifeline.filtered .events-container .event-card + .event-card { margin-top: 0; }

.events-container.collapsed {
  max-height: 0 !important;
}

/* ---------- Event Card ---------- */
.event-card {
  position: relative;
  width: 47%;
  background: var(--glass-bg, rgba(255,255,255,0.62));
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  border: 1px solid var(--glass-edge, rgba(255,255,255,0.9));
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 8px 24px -16px rgba(60, 20, 80, 0.22);
  cursor: pointer;
  transition: all 0.3s ease;
}

.event-card.hidden-by-filter {
  display: none;
}

.event-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.event-card.left {
  margin-left: auto;
  margin-right: 53%;
  text-align: right;
}

.event-card.right {
  margin-left: 53%;
  margin-right: auto;
  text-align: left;
}

/* ---------- Connection Dot ---------- */
.event-card::before {
  content: '';
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background: white;
  border: 3px solid var(--tsinghua, #660874);
  border-radius: 50%;
  transform: translateY(-50%);
}

.event-card.left::before {
  right: -6.4%;
}

.event-card.right::before {
  left: -6.4%;
}

/* ---------- Card Header ---------- */
.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.event-card.left .event-header {
  flex-direction: row;
}

.event-card.right .event-header {
  flex-direction: row-reverse;
}

/* ---------- Event Type Tag ---------- */
.event-tag {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  color: white;
}

.tag-award       { background: #f59e0b; }
.tag-honor       { background: #a855f7; }
.tag-publication { background: #3b82f6; }
.tag-milestone   { background: #10b981; }
.tag-project     { background: #06b6d4; }
.tag-talk        { background: #ef4444; }
.tag-service     { background: #8b5cf6; }
.tag-exchange    { background: #ec4899; }

.event-icon {
  font-size: 1.5rem;
}

/* ---------- Event Title ---------- */
.event-title {
  font-family: var(--display, Georgia, serif);
  font-size: 1.05rem;
  font-weight: 500;
  color: var(--ink-strong, #1e293b);
  line-height: 1.4;
}

/* ---------- Event Details (click to expand) ---------- */
.event-details {
  display: none;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--rule, #e2e8f0);
}

.event-card.expanded .event-details {
  display: block;
}

.event-date {
  font-family: var(--ui, sans-serif);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--tsinghua, #94a3b8);
}

.event-description {
  font-size: 0.9rem;
  color: var(--ink-soft, #64748b);
  margin-top: 0.25rem;
}

/* ---------- Bottom End Dot ---------- */
.lifeline-end {
  display: flex;
  justify-content: center;
  padding: 1.5rem 0;
  position: relative;
  z-index: 10;
}

.lifeline-end-dot {
  width: 1.5rem;
  height: 1.5rem;
  background: var(--tsinghua-pale, #cbd5e1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lifeline-end-dot::before {
  content: '';
  width: 0.5rem;
  height: 0.5rem;
  background: var(--tsinghua, #64748b);
  border-radius: 50%;
}

/* ---------- Empty State ---------- */
.lifeline-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #94a3b8;
  font-size: 0.95rem;
  display: none;
  position: relative;
  z-index: 10;
}

/* ---------- Mobile Responsive ---------- */
@media (max-width: 768px) {
  .lifeline::before {
    left: 20px;
  }

  .event-card {
    width: calc(100% - 50px);
    margin-left: 50px !important;
    margin-right: 0 !important;
    text-align: left !important;
  }

  .event-card .event-header {
    flex-direction: row-reverse !important;
  }

  .event-card::before {
    left: -40px !important;
    right: auto !important;
  }

  /* single column on mobile → no overlap stagger, restore vertical spacing */
  .events-container { gap: 0.75rem; }
  .events-container .event-card + .event-card { margin-top: 0; }

  .lifeline-toolbar {
    gap: 0.375rem;
  }

  .filter-pill {
    padding: 0.3rem 0.625rem;
    font-size: 0.7rem;
  }
}
</style>

<!-- ==================== Data Processing ==================== -->
{% assign events_by_year = site.data.lifeline.events | group_by: "year" | sort: "name" | reverse %}
{% assign total_years = events_by_year | size %}
{% assign total_events = site.data.lifeline.events | size %}

{% assign award_count = site.data.lifeline.events | where: "type", "award" | size %}
{% assign honor_count = site.data.lifeline.events | where: "type", "honor" | size %}
{% assign talk_count = site.data.lifeline.events | where: "type", "talk" | size %}
{% assign project_count = site.data.lifeline.events | where: "type", "project" | size %}
{% assign service_count = site.data.lifeline.events | where: "type", "service" | size %}
{% assign publication_count = site.data.lifeline.events | where: "type", "publication" | size %}
{% assign exchange_count = site.data.lifeline.events | where: "type", "exchange" | size %}

<!-- ==================== Page Structure ==================== -->
<div class="lifeline-header">
  <h2><span class="only-en">Life Line</span><span class="only-zh">人生轨迹</span></h2>
  <p class="lifeline-hint">
    <span id="visible-count">{{ total_events }}</span>
    <span class="only-en">Moments · {{ total_years }} Years</span><span class="only-zh">条记录 · {{ total_years }} 年</span>
    <br><small><span class="only-en">Click nodes to expand · Filter by type</span><span class="only-zh">点击节点展开 · 按类型筛选</span></small>
  </p>

  <!-- Toolbar: filter + expand controls on one row -->
  <div class="lifeline-toolbar">
    <button class="filter-pill active" data-type="all" onclick="filterByType('all', this)">
      <span class="only-en">All</span><span class="only-zh">全部</span> <span class="filter-count">{{ total_events }}</span>
    </button>
    <button class="filter-toggle" id="filter-toggle" onclick="toggleFilterTypes()" aria-expanded="false">
      <span class="only-en">By type</span><span class="only-zh">按类型</span>
      <span class="filter-chev">▾</span>
    </button>
    <span class="toolbar-divider"></span>
    <button class="lifeline-btn" onclick="expandAllYears()"><span class="only-en">Expand All</span><span class="only-zh">全部展开</span></button>
    <button class="lifeline-btn" onclick="collapseAllYears()"><span class="only-en">Collapse All</span><span class="only-zh">全部收起</span></button>
  </div>

  <!-- Category sub-filters (collapsible, drops below the toolbar) -->
  <div class="filter-pills-extra" id="filter-extra">
    {% if award_count > 0 %}
    <button class="filter-pill" data-type="award" onclick="filterByType('award', this)">
      🏆 <span class="only-en">{{ site.data.lifeline.tags.award }}</span><span class="only-zh">{{ site.data.lifeline.tags_zh.award }}</span> <span class="filter-count">{{ award_count }}</span>
    </button>
    {% endif %}
    {% if honor_count > 0 %}
    <button class="filter-pill" data-type="honor" onclick="filterByType('honor', this)">
      🎖️ <span class="only-en">{{ site.data.lifeline.tags.honor }}</span><span class="only-zh">{{ site.data.lifeline.tags_zh.honor }}</span> <span class="filter-count">{{ honor_count }}</span>
    </button>
    {% endif %}
    {% if talk_count > 0 %}
    <button class="filter-pill" data-type="talk" onclick="filterByType('talk', this)">
      🎤 <span class="only-en">{{ site.data.lifeline.tags.talk }}</span><span class="only-zh">{{ site.data.lifeline.tags_zh.talk }}</span> <span class="filter-count">{{ talk_count }}</span>
    </button>
    {% endif %}
    {% if project_count > 0 %}
    <button class="filter-pill" data-type="project" onclick="filterByType('project', this)">
      📋 <span class="only-en">{{ site.data.lifeline.tags.project }}</span><span class="only-zh">{{ site.data.lifeline.tags_zh.project }}</span> <span class="filter-count">{{ project_count }}</span>
    </button>
    {% endif %}
    {% if service_count > 0 %}
    <button class="filter-pill" data-type="service" onclick="filterByType('service', this)">
      🤝 <span class="only-en">{{ site.data.lifeline.tags.service }}</span><span class="only-zh">{{ site.data.lifeline.tags_zh.service }}</span> <span class="filter-count">{{ service_count }}</span>
    </button>
    {% endif %}
    {% if publication_count > 0 %}
    <button class="filter-pill" data-type="publication" onclick="filterByType('publication', this)">
      📜 <span class="only-en">{{ site.data.lifeline.tags.publication }}</span><span class="only-zh">{{ site.data.lifeline.tags_zh.publication }}</span> <span class="filter-count">{{ publication_count }}</span>
    </button>
    {% endif %}
    {% if exchange_count > 0 %}
    <button class="filter-pill" data-type="exchange" onclick="filterByType('exchange', this)">
      ✈️ <span class="only-en">{{ site.data.lifeline.tags.exchange }}</span><span class="only-zh">{{ site.data.lifeline.tags_zh.exchange }}</span> <span class="filter-count">{{ exchange_count }}</span>
    </button>
    {% endif %}
  </div>
</div>

<div class="lifeline">
  {% for year in events_by_year %}
  <div class="year-section" data-year="{{ year.name }}">
    <div class="year-marker" onclick="toggleYear('{{ year.name }}')">
      <span class="year-label">
        {{ year.name }}
        <span class="year-count" id="count-{{ year.name }}">{{ year.items | size }}</span>
        <span class="year-chevron" id="chevron-{{ year.name }}">▼</span>
      </span>
    </div>

    <div class="events-container" id="events-{{ year.name }}">
      {% for event in year.items %}
      {% assign position = forloop.index | modulo: 2 %}
      <div class="event-card {% if position == 1 %}left{% else %}right{% endif %}" data-type="{{ event.type }}" onclick="toggleCard(this)">
        <div class="event-header">
          <span class="event-tag tag-{{ event.type }}">
            <span class="only-en">{{ site.data.lifeline.tags[event.type] }}</span>
            <span class="only-zh">{{ site.data.lifeline.tags_zh[event.type] | default: site.data.lifeline.tags[event.type] }}</span>
          </span>
          <span class="event-icon">{% if event.type == 'award' %}{{ event.icon }}{% else %}{{ site.data.lifeline.icons[event.type] | default: event.icon }}{% endif %}</span>
        </div>
        <div class="event-title">
          <span class="only-en">{{ event.title }}</span>
          <span class="only-zh">{% if event.description and event.description != "" %}{{ event.description }}{% else %}{{ event.title }}{% endif %}</span>
        </div>
        <div class="event-details">
          <span class="event-date">{{ event.date }}</span>
          {% if event.description and event.description != "" %}
          <p class="event-description">
            <span class="only-en">{{ event.description }}</span>
            <span class="only-zh">{{ event.title }}</span>
          </p>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endfor %}

  <div class="lifeline-empty" id="lifeline-empty">
    No events found for this category.
  </div>

  <div class="lifeline-end">
    <div class="lifeline-end-dot"></div>
  </div>
</div>

<!-- ==================== Scripts ==================== -->
<script>
var currentFilter = 'all';

/* On load: measure real content heights (replaces hardcoded max-height) */
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.events-container').forEach(function(el) {
    el.style.maxHeight = el.scrollHeight + 'px';
  });
});

/* Toggle a single year open/closed */
function toggleYear(year) {
  var container = document.getElementById('events-' + year);
  var chevron = document.getElementById('chevron-' + year);
  if (container.classList.contains('collapsed')) {
    container.classList.remove('collapsed');
    container.style.maxHeight = container.scrollHeight + 'px';
    chevron.textContent = '▼';
  } else {
    container.style.maxHeight = container.scrollHeight + 'px';
    requestAnimationFrame(function() {
      container.classList.add('collapsed');
      chevron.textContent = '▶';
    });
  }
}

/* Toggle a card's detail section */
function toggleCard(card) {
  card.classList.toggle('expanded');
  var container = card.closest('.events-container');
  if (container && !container.classList.contains('collapsed')) {
    setTimeout(function() {
      container.style.maxHeight = container.scrollHeight + 'px';
    }, 60);
  }
}

/* Expand all year sections */
function expandAllYears() {
  document.querySelectorAll('.year-section:not(.hidden-by-filter)').forEach(function(section) {
    var el = section.querySelector('.events-container');
    var chevron = section.querySelector('.year-chevron');
    if (el) {
      el.classList.remove('collapsed');
      el.style.maxHeight = el.scrollHeight + 'px';
    }
    if (chevron) chevron.textContent = '▼';
  });
}

/* Collapse all year sections */
function collapseAllYears() {
  document.querySelectorAll('.year-section:not(.hidden-by-filter)').forEach(function(section) {
    var el = section.querySelector('.events-container');
    var chevron = section.querySelector('.year-chevron');
    if (el) {
      el.style.maxHeight = el.scrollHeight + 'px';
      requestAnimationFrame(function() { el.classList.add('collapsed'); });
    }
    if (chevron) chevron.textContent = '▶';
  });
}

/* Re-alternate left/right positions for visible cards within each year */
function repositionCards() {
  document.querySelectorAll('.year-section:not(.hidden-by-filter)').forEach(function(section) {
    var visibleCards = section.querySelectorAll('.event-card:not(.hidden-by-filter)');
    visibleCards.forEach(function(card, i) {
      card.classList.remove('left', 'right');
      card.classList.add(i % 2 === 0 ? 'left' : 'right');
    });
  });
}

/* Filter timeline by event type */
function toggleFilterTypes() {
  var extra = document.getElementById('filter-extra');
  var tog = document.getElementById('filter-toggle');
  if (!extra || !tog) return;
  var open = extra.classList.toggle('open');
  tog.classList.toggle('open', open);
  tog.setAttribute('aria-expanded', open ? 'true' : 'false');
}

function filterByType(type, btn) {
  currentFilter = type;

  /* Disable the interleave stagger while a specific type is active
     (hidden cards otherwise break the negative-margin adjacency → clipping). */
  var timeline = document.querySelector('.lifeline');
  if (timeline) timeline.classList.toggle('filtered', type !== 'all');

  /* Keep the type panel open while a specific category is active so the
     selected pill stays visible; collapse it again when returning to "All". */
  var extra = document.getElementById('filter-extra');
  var tog = document.getElementById('filter-toggle');
  if (extra && tog) {
    var shouldOpen = type !== 'all';
    extra.classList.toggle('open', shouldOpen);
    tog.classList.toggle('open', shouldOpen);
    tog.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
  }

  /* Update active pill */
  document.querySelectorAll('.filter-pill').forEach(function(p) {
    p.classList.remove('active');
  });
  btn.classList.add('active');

  /* Show/hide event cards */
  var visibleCount = 0;
  document.querySelectorAll('.event-card').forEach(function(card) {
    if (type === 'all' || card.dataset.type === type) {
      card.classList.remove('hidden-by-filter');
      visibleCount++;
    } else {
      card.classList.add('hidden-by-filter');
      card.classList.remove('expanded');
    }
  });

  document.getElementById('visible-count').textContent = visibleCount;

  /* Hide empty year sections; update per-year counts */
  var anyYearVisible = false;
  document.querySelectorAll('.year-section').forEach(function(section) {
    var cards = section.querySelectorAll('.event-card:not(.hidden-by-filter)');
    var countEl = section.querySelector('.year-count');
    if (cards.length === 0) {
      section.classList.add('hidden-by-filter');
    } else {
      section.classList.remove('hidden-by-filter');
      anyYearVisible = true;
      if (countEl) countEl.textContent = cards.length;
    }
  });

  /* Re-alternate left/right after filter */
  repositionCards();

  /* Recalculate container heights */
  setTimeout(function() {
    document.querySelectorAll('.year-section:not(.hidden-by-filter) .events-container').forEach(function(el) {
      if (!el.classList.contains('collapsed')) {
        el.style.maxHeight = el.scrollHeight + 'px';
      }
    });
  }, 60);

  /* Empty state */
  document.getElementById('lifeline-empty').style.display = anyYearVisible ? 'none' : 'block';
}
</script>
