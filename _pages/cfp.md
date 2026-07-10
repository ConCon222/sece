---
layout: page
title: Call for Papers
title_zh: 期刊征稿
permalink: /cfp/
description: Curated academic opportunities in Edu. Auto-updated daily.
description_zh: 精选的教育领域学术征稿信息，每日自动更新。
nav: true
nav_zh: 期刊征稿
nav_order: 3
---

{% assign all_tags = site.data.cfps | map: 'tag' | join: ',' | split: ',' | uniq | sort %}
<style>
  /* Search & Filter Bar */
  .cfp-filter-section {
    background: var(--glass-bg-soft, rgba(255,255,255,0.42));
    border: 1px solid var(--glass-edge, rgba(255,255,255,0.9));
    backdrop-filter: blur(16px) saturate(160%);
    -webkit-backdrop-filter: blur(16px) saturate(160%);
    padding: 16px 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px -14px rgba(60,20,80,0.18);
  }
  .cfp-filter-section .row > div {
    margin-bottom: 8px;
  }

  /* Deadline badges */
  .deadline-active { background-color: #28a745; color: white; }
  .deadline-urgent { background-color: #fd7e14; color: white; }
  .deadline-expired { background-color: #6c757d; color: white; }
  .deadline-tba { background-color: #ffc107; color: #212529; }
  .countdown-text {
    font-size: 0.75rem;
    color: #dc3545;
    font-weight: 600;
    margin-top: 2px;
  }
  .countdown-text.comfortable {
    color: #28a745;
  }

  /* Details box */
  .cfp-details-box {
    background-color: var(--tsinghua-wash, #f1e6f5);
    border-left: 3px solid var(--tsinghua, #660874);
    padding: 10px 15px;
    margin-top: 10px;
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
  }

  /* Topic cell: title + inline scope + clear CTA */
  .cfp-title {
    font-family: var(--display, Georgia, serif);
    font-weight: 600;
    font-size: 1.02rem;
    line-height: 1.3;
    color: var(--ink-strong, #100716);
  }
  .cfp-title:hover { color: var(--tsinghua, #660874); }
  .cfp-scope {
    margin: 6px 0 9px;
    font-size: 0.85rem;
    line-height: 1.5;
    color: var(--ink-faint, #645a72);
  }
  .cfp-row-actions {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }
  .cfp-cta {
    display: inline-flex;
    align-items: center;
    font-family: var(--ui, sans-serif);
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--tsinghua, #660874) !important;
    background: rgba(102, 8, 116, 0.07);
    border: 1px solid var(--tsinghua-pale, #d9bee0);
    padding: 5px 14px;
    border-radius: 999px;
    transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
  }
  .cfp-cta:hover {
    background: var(--tsinghua, #660874);
    border-color: var(--tsinghua, #660874);
    color: #fff !important;
    transform: translateY(-1px);
  }
  .cfp-more summary {
    font-family: var(--ui, sans-serif);
    font-size: 0.8rem;
    color: var(--tsinghua, #660874);
    cursor: pointer;
    list-style: none;
  }
  .cfp-more summary::-webkit-details-marker { display: none; }
  .cfp-more summary::before { content: "＋ "; }
  .cfp-more[open] summary::before { content: "− "; }

  /* Sortable headers */
  .cfp-sortable { cursor: pointer; user-select: none; white-space: nowrap; }
  .cfp-sort-icon::after { content: "⇅"; font-size: 0.7rem; opacity: 0.4; margin-left: 3px; }
  .cfp-sortable:hover .cfp-sort-icon::after { opacity: 0.8; }
  .cfp-sortable.sort-asc, .cfp-sortable.sort-desc { color: var(--tsinghua, #660874); }
  .cfp-sortable.sort-asc .cfp-sort-icon::after { content: "↑"; opacity: 1; color: var(--tsinghua, #660874); }
  .cfp-sortable.sort-desc .cfp-sort-icon::after { content: "↓"; opacity: 1; color: var(--tsinghua, #660874); }
  .cfp-meta-label {
    font-weight: 600;
    color: var(--ink-soft, #4d3f5c);
  }

  /* Tag badges */
  .tag-badge {
    font-size: 0.7rem;
    margin-right: 2px;
    margin-bottom: 2px;
    display: inline-block;
  }

  /* Journal link to rankings */
  .cfp-journal-link {
    font-size: 0.7rem;
    color: var(--tsinghua, #660874);
    text-decoration: none;
    margin-left: 4px;
  }
  .cfp-journal-link:hover {
    text-decoration: underline;
  }

  /* Empty state */
  .cfp-empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #6c757d;
    display: none;
  }

  /* Toggle switch */
  .toggle-label {
    font-size: 0.85rem;
    color: #495057;
    cursor: pointer;
    user-select: none;
  }
  .toggle-label input {
    margin-right: 4px;
  }

  /* Results count */
  .results-count {
    font-size: 0.8rem;
    color: #6c757d;
    margin-bottom: 8px;
  }

  /* Mobile */
  @media (max-width: 768px) {
    .table-responsive { font-size: 0.9rem; }
    .cfp-filter-section { padding: 12px; }
    #cfp-table,
    #cfp-table tbody { display: block; width: 100%; }
    #cfp-table thead { display: none; }
    #cfp-table .cfp-row {
      display: block;
      margin: 0;
      padding: 16px;
      border-bottom: 1px solid rgba(102, 8, 116, 0.12);
    }
    #cfp-table .cfp-row:last-child { border-bottom: 0; }
    #cfp-table .cfp-row > td {
      display: block;
      width: 100%;
      min-width: 0;
      padding: 8px 0;
      border: 0;
    }
    #cfp-table .cfp-row > td[data-label="Deadline"],
    #cfp-table .cfp-row > td[data-label="Journal"] { display: inline-block; width: calc(50% - 4px); vertical-align: top; }
    #cfp-table .cfp-row > td[data-label="Topic & Details"] { padding-top: 14px; }
    .cfp-mobile-label {
      display: block;
      margin-bottom: 5px;
      font-family: var(--ui, sans-serif);
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      color: var(--ink-faint, #645a72);
      text-transform: uppercase;
    }
    .cfp-title { font-size: 1.08rem; line-height: 1.35; }
    .cfp-scope { font-size: 0.9rem; }
    .cfp-cta { min-height: 40px; align-items: center; }
  }
  @media (min-width: 769px) { .cfp-mobile-label { display: none; } }

  .cfp-full-scope { white-space: pre-wrap; }
  .cfp-pagination {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 18px;
  }
  .cfp-page-btn {
    min-width: 36px;
    height: 36px;
    padding: 0 10px;
    border: 1px solid var(--tsinghua-pale, #d9bee0);
    border-radius: 9px;
    background: rgba(255, 255, 255, 0.68);
    color: var(--ink-soft, #4d3f5c);
    font-family: var(--ui, sans-serif);
  }
  .cfp-page-btn.active { background: var(--tsinghua, #660874); border-color: var(--tsinghua, #660874); color: #fff; }
  .cfp-page-btn:disabled { opacity: 0.42; }
</style>

<!-- Search & Filter Section -->
{% include context_rail.liquid items="cfp-filters::Filters::筛选|cfp-results::Current calls::征稿列表|cfp-notes::Notes::说明" %}
<div class="cfp-filter-section context-rail-target" id="cfp-filters">
  <div class="row align-items-center">
    <div class="col-md-4">
      <input type="text" id="cfp-search" class="form-control form-control-sm" placeholder="Search journal or topic...">
    </div>
    <div class="col-md-3">
      <select id="cfp-tag-filter" class="form-control form-control-sm">
        <option value="">All Tags</option>
        {% for tag in all_tags %}
          {% if tag != "" %}
          <option value="{{ tag | strip }}">{{ tag | strip }}</option>
          {% endif %}
        {% endfor %}
      </select>
    </div>
    <div class="col-md-3">
      <select id="cfp-publisher-filter" class="form-control form-control-sm">
        <option value="">All Publishers</option>
        {% assign all_publishers = site.data.cfps | map: 'publisher' | compact | uniq | sort %}
        {% for p in all_publishers %}{% if p != "" %}<option value="{{ p }}">{{ p }}</option>{% endif %}{% endfor %}
      </select>
    </div>
    <div class="col-md-2 text-right">
      <label class="toggle-label mb-0">
        <input type="checkbox" id="cfp-show-expired"> Show Expired
      </label>
    </div>
  </div>
</div>

<div id="cfp-results" class="context-rail-target">
<div class="results-count" id="cfp-results-count"></div>

<div class="table-responsive">
  <table class="table table-hover" id="cfp-table" data-source="{{ '/assets/data/cfp-browser.json' | relative_url }}">
    <thead>
      <tr>
        <th width="18%" class="cfp-sortable" data-sort="deadline">Deadline <span class="cfp-sort-icon"></span></th>
        <th width="15%" class="cfp-sortable" data-sort="journal">Journal <span class="cfp-sort-icon"></span></th>
        <th width="55%">Topic &amp; Details</th>
        <th width="12%">Tags</th>
      </tr>
    </thead>
    <tbody id="cfp-table-body"><tr><td colspan="4">Loading calls for papers…</td></tr></tbody>
  </table>
</div>

<nav class="cfp-pagination" id="cfp-pagination" aria-label="Call for papers pages"></nav>

<!-- Empty state -->
<div class="cfp-empty-state" id="cfp-empty-state">
  <p>No matching Call for Papers found.<br>Try adjusting your filters.</p>
</div>
</div>

<script defer src="{{ '/assets/js/cfp-table.js' | relative_url | bust_file_cache }}"></script>

<hr class="mt-5 mb-3">
<p class="text-muted small text-center context-rail-target" id="cfp-notes">
  <em>Disclaimer: The information on this page is for reference only. Deadlines and details may change. Please visit the official links to verify the latest information.</em><br>
  <em>免责声明：本页面信息仅供参考，截止日期可能有变动，请访问原链接确认最新信息，一切以官方网站为准。</em>
</p>

{% include cfp_recommender.html %}
{% include wechat_qr.html %}
