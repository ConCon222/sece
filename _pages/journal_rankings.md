---
layout: page
permalink: /jrank/
title: Journal Rankings
title_zh: 期刊排名
description: HM Score combines journal quality metrics and author-friendliness
description_zh: HM 友好性指数综合了期刊质量指标与对作者的友好程度。
nav: true
nav_zh: 期刊排名
nav_order: 4
---

{% assign all_tags = site.data.jrank | map: 'tag' | join: ',' | split: ',' | uniq | sort %}

<div class="journal-rankings">
  <!-- What this is -->
  <p class="jr-intro">
    <span class="only-en">A curated dashboard of education &amp; related-field journals, ranked by an <strong>HM friendliness score</strong> that blends impact metrics (IF · CiteScore · CAS division) with how author-friendly each journal is (acceptance rate · decision speed), so you can quickly see <em>where it's worth submitting</em>.</span>
    <span class="only-zh">教育及相关领域期刊的精选看板，按 <strong>HM 友好性指数</strong> 排名——它综合了影响力指标（影响因子 · CiteScore · 中科院分区）与对作者的友好程度（录用率 · 审稿速度），帮你一眼看出<em>值得往哪里投稿</em>。</span>
  </p>

  <!-- At-a-glance statistics -->
  <div class="statistics-section mb-4">
    <div class="row">
      <div class="col-6 col-md-3"><div class="stat-card"><h6><span class="only-en">Total Journals</span><span class="only-zh">期刊总数</span></h6><span id="total-journals">{{ site.data.jrank | size }}</span></div></div>
      <div class="col-6 col-md-3"><div class="stat-card"><h6><span class="only-en">Q1 Journals</span><span class="only-zh">Q1 期刊</span></h6><span id="q1-count">{% assign q1_count = 0 %}{% for journal in site.data.jrank %}{% if journal.purple_quartile contains 'Q1' %}{% assign q1_count = q1_count | plus: 1 %}{% endif %}{% endfor %}{{ q1_count }}</span></div></div>
      <div class="col-6 col-md-3"><div class="stat-card"><h6><span class="only-en">Publishers</span><span class="only-zh">出版商</span></h6><span>5</span></div></div>
      <div class="col-6 col-md-3"><div class="stat-card"><h6><span class="only-en">Last Updated</span><span class="only-zh">最近更新</span></h6><span id="last-updated">{{ site.time | date: "%Y-%m-%d" }}</span></div></div>
    </div>
  </div>

  <!-- Search and Filter Section -->
  <div class="search-filter-section mb-4">
    <div class="row">
      <div class="col-md-4">
        <input type="text" id="journal-search" class="form-control form-control-sm" placeholder="Search journals by name or tag...">
      </div>
      <div class="col-md-2">
        <select id="quartile-filter" class="form-control form-control-sm">
          <option value="">All Quartiles</option>
          <option value="Q1">Q1</option>
          <option value="Q2">Q2</option>
          <option value="Q3">Q3</option>
          <option value="Q4">Q4</option>
        </select>
      </div>
      <div class="col-md-2">
        <select id="publisher-filter" class="form-control form-control-sm">
          <option value="">All Publishers</option>
          <option value="Springer">Springer</option>
          <option value="Wiley">Wiley</option>
          <option value="Elsevier">Elsevier</option>
          <option value="Taylor & Francis">Taylor & Francis</option>
          <option value="SAGE">SAGE</option>
        </select>
      </div>
      <div class="col-md-2">
        <select id="tag-filter" class="form-control form-control-sm">
          <option value="">All Tags</option>
          {% for tag in all_tags %}
            {% if tag != "" %}
            <option value="{{ tag | strip | downcase }}">{{ tag | strip }}</option>
            {% endif %}
          {% endfor %}
        </select>
      </div>
      <div class="col-md-2 text-right">
        <span class="results-count" id="jr-results-count"></span>
      </div>
    </div>
  </div>

  <!-- Journal Rankings Table -->
  <div class="table-responsive">
    <table class="table table-striped table-hover" id="journal-table">
      <thead>
        <tr>
          <th class="sortable jr-th" data-sort="name" data-tip-en="Journal name & publisher" data-tip-zh="期刊名称与出版商">Journal Name <span class="sort-icon"></span></th>
          <th class="sortable jr-th" data-sort="hm" data-tip-en="HM friendliness score: blends quality with how author-friendly the journal is (higher is better)" data-tip-zh="HM 友好性指数：综合期刊质量与对作者的友好度，越高越好">HM <span class="sort-icon"></span></th>
          <th class="sortable jr-th" data-sort="purple" data-tip-en="Impact Factor & JCR quartile (Clarivate)" data-tip-zh="影响因子（IF）与 JCR 分区（科睿唯安）">Purple<br><small>(IF)</small> <span class="sort-icon"></span></th>
          <th class="sortable jr-th" data-sort="orange" data-tip-en="Scopus CiteScore & quartile (Elsevier)" data-tip-zh="Scopus CiteScore 与分区（爱思唯尔）">Orange<br><small>(CiteScore)</small> <span class="sort-icon"></span></th>
          <th class="jr-th" data-tip-en="Chinese Academy of Sciences subject division (中科院大类分区)" data-tip-zh="中科院分区（大类）">Red</th>
          <th class="sortable jr-th" data-sort="decision" data-tip-en="Average time to first editorial decision (days)" data-tip-zh="平均首次审稿决定时长（天）">First<br><small>Decision</small> <span class="sort-icon"></span></th>
          <th class="sortable jr-th" data-sort="accept" data-tip-en="Acceptance rate" data-tip-zh="录用率">Accept<br><small>Rate</small> <span class="sort-icon"></span></th>
          <th class="jr-th" data-tip-en="Review / acceptance / publication times & article counts" data-tip-zh="审稿 / 录用 / 出版周期与发文量">More</th>
          <th class="jr-th" data-tip-en="Subject areas" data-tip-zh="学科领域">Tags</th>
        </tr>
      </thead>
      <tbody id="journal-tbody">
        {% assign sorted_journals = site.data.jrank | sort: 'purple_score' | reverse %}
        {% for journal in sorted_journals %}
        {% assign journal_data = site.data.journal_rank | where: "name", journal.journal | first %}
        <tr data-journal="{{ journal.journal | downcase }}"
            data-publisher="{{ journal.publisher | downcase }}"
            data-quartile="{{ journal.purple_quartile }}"
            data-tags="{{ journal.tag | join: ',' | downcase }}"
            data-hm="{{ journal.hm_score | default: 0 }}"
            data-purple="{{ journal.purple_score | default: 0 }}"
            data-orange="{{ journal.orange_score | default: 0 }}"
            data-decision="{{ journal.first_decision_time | remove: ' days' | default: 9999 }}"
            data-accept="{{ journal.acceptance_rate | remove: '%' | default: 0 }}"
            data-name="{{ journal.journal }}">
          <!-- Journal Name -->
          <td>
            <strong>{{ journal.journal }}</strong>
            {% if journal.publisher and journal.publisher != "" %}
              <br><small class="text-muted">{{ journal.publisher }}</small>
            {% endif %}
            {% if journal_data.url %}
              <a href="{{ journal_data.url }}" target="_blank" class="ml-1" title="Publisher page">
                <i class="fas fa-external-link-alt" style="font-size:0.7rem;"></i>
              </a>
            {% endif %}
            <a href="/cfp/?q={{ journal.journal | url_encode }}" class="jr-cfp-link" title="Search CFPs for this journal">CFP</a>
          </td>
          <!-- HM Score -->
          <td>
            {% if journal.hm_score and journal.hm_score != "" %}
              <span class="hm-score" data-score="{{ journal.hm_score }}">
                {{ journal.hm_score }}
              </span>
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <!-- Purple (JCR) -->
          <td>
            {% if journal.purple_quartile and journal.purple_quartile != "" %}
              <span class="badge badge-purple">{{ journal.purple_quartile }}</span>
              {% if journal.purple_score and journal.purple_score != "" %}
                <br><small>{{ journal.purple_score }}</small>
              {% endif %}
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <!-- Orange (Scopus) -->
          <td>
            {% if journal.orange_quartile and journal.orange_quartile != "" %}
              <span class="badge badge-orange">{{ journal.orange_quartile }}</span>
              {% if journal.orange_score and journal.orange_score != "" %}
                <br><small>
                  {% if journal_data.sourceid %}
                    <a href="https://www.scopus.com/sourceid/{{ journal_data.sourceid }}" target="_blank">{{ journal.orange_score }}</a>
                  {% else %}
                    {{ journal.orange_score }}
                  {% endif %}
                </small>
              {% endif %}
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <!-- Red (CAS) -->
          <td>
            {% if journal.red_division and journal.red_division != "" %}
              <span class="badge badge-red">{{ journal.red_division }}</span>
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <!-- First Decision -->
          <td>
            {% if journal.first_decision_time and journal.first_decision_time != "" %}
              {{ journal.first_decision_time | remove: ' days' }}d
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <!-- Accept Rate -->
          <td>
            {% if journal.acceptance_rate and journal.acceptance_rate != "" %}
              {{ journal.acceptance_rate }}
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <!-- More (expandable details) -->
          <td>
            {% assign has_extra = false %}
            {% if journal.review_time or journal.acceptance_time or journal.publication_time or journal.documents_current_year %}
              {% assign has_extra = true %}
            {% endif %}
            {% if has_extra %}
            <details class="jr-details">
              <summary class="small text-primary" style="cursor:pointer;white-space:nowrap;">Details</summary>
              <div class="jr-details-box">
                {% if journal.review_time and journal.review_time != "" %}
                  <div><small><strong>Review:</strong> {{ journal.review_time | remove: ' days' }}d</small></div>
                {% endif %}
                {% if journal.acceptance_time and journal.acceptance_time != "" %}
                  <div><small><strong>To Accept:</strong> {{ journal.acceptance_time | remove: ' days' }}d</small></div>
                {% endif %}
                {% if journal.publication_time and journal.publication_time != "" %}
                  <div><small><strong>To Publish:</strong> {{ journal.publication_time | remove: ' days' }}d</small></div>
                {% endif %}
                {% if journal.documents_current_year and journal.documents_current_year != "" %}
                  <div><small><strong>Articles:</strong> {{ journal.documents_current_year }}</small></div>
                {% endif %}
                {% if journal.documents_last_year and journal.documents_last_year != "" %}
                  <div><small><strong>Last Year:</strong> {{ journal.documents_last_year }}</small></div>
                {% endif %}
              </div>
            </details>
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <!-- Tags -->
          <td class="tags-cell">
            {% if journal.tag %}
              {% for tag in journal.tag %}
                <span class="badge badge-light border tag-badge">{{ tag }}</span>
              {% endfor %}
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Pagination controls -->
  <nav class="jr-pagination" id="jr-pagination" aria-label="Journal table pages"></nav>

  <!-- Empty state -->
  <div class="jr-empty-state" id="jr-empty-state" style="display:none;">
    <p><span class="only-en">No matching journals found.<br>Try adjusting your filters.</span><span class="only-zh">没有匹配的期刊。<br>试试调整筛选条件。</span></p>
  </div>
</div>

<style>
.journal-rankings {
  padding: 20px 0;
}

.search-filter-section {
  background: var(--glass-bg-soft, rgba(255,255,255,0.42));
  border: 1px solid var(--glass-edge, rgba(255,255,255,0.9));
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  padding: 16px 20px;
  border-radius: 16px;
  margin-bottom: 20px;
  box-shadow: 0 8px 24px -14px rgba(60,20,80,0.18);
}

.search-filter-section .row > div {
  margin-bottom: 6px;
}

.results-count {
  font-size: 0.8rem;
  color: #6c757d;
  line-height: 31px;
}

.badge-purple {
  background-color: var(--tsinghua, #660874);
  color: white;
}

.badge-orange {
  background-color: #fd7e14;
  color: white;
}

.badge-red {
  background-color: #dc3545;
  color: white;
}

.hm-score {
  font-weight: bold;
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
  display: inline-block;
  min-width: 35px;
  text-align: center;
  background-color: #6c757d;
}

/* Sortable headers */
.sortable {
  cursor: pointer;
  user-select: none;
  position: relative;
  transition: background-color 0.2s ease;
}
.sortable:hover {
  background-color: rgba(102, 8, 116, 0.06);
}
/* sort glyph sits in a subtle rounded chip so it reads as a control */
.sort-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.05em;
  height: 1.05em;
  margin-left: 4px;
  font-size: 0.72rem;
  line-height: 1;
  border-radius: 4px;
  background: rgba(102, 8, 116, 0.08);
  color: var(--ink-faint, #645a72);
  opacity: 0.7;
  transition: opacity 0.2s ease, background 0.2s ease, color 0.2s ease;
}
.sort-icon::after { content: '⇅'; }
.sortable:hover .sort-icon { opacity: 1; background: rgba(102, 8, 116, 0.16); }

/* active sorted column: purple arrow + purple underline bar (matches CFP) */
.sortable.sort-asc,
.sortable.sort-desc {
  background-color: rgba(102, 8, 116, 0.05);
  box-shadow: inset 0 -3px 0 0 var(--tsinghua, #660874);
  color: var(--tsinghua, #660874);
}
.sortable.sort-asc .sort-icon,
.sortable.sort-desc .sort-icon {
  opacity: 1;
  color: #fff;
  background: var(--tsinghua, #660874);
  font-weight: 700;
}
.sortable.sort-asc .sort-icon::after { content: '↑'; }
.sortable.sort-desc .sort-icon::after { content: '↓'; }

/* Cross-link to CFP */
.jr-cfp-link {
  font-size: 0.65rem;
  color: var(--tsinghua, #660874);
  text-decoration: none;
  margin-left: 4px;
  border: 1px solid var(--tsinghua-pale, #d9bee0);
  padding: 0 3px;
  border-radius: 4px;
}
.jr-cfp-link:hover {
  background-color: var(--tsinghua, #660874);
  color: white;
  text-decoration: none;
}

/* More details column */
.jr-details-box {
  padding: 4px 0;
  white-space: nowrap;
}

/* Empty state */
.jr-empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
}

.statistics-section {
  background: var(--glass-bg-soft, rgba(255,255,255,0.42));
  border: 1px solid var(--glass-edge, rgba(255,255,255,0.9));
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 8px 24px -14px rgba(60,20,80,0.18);
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-height: 82px;
  height: 100%;
  text-align: center;
  padding: 12px 10px;
  background: rgba(255,255,255,0.7);
  border: 1px solid var(--rule, rgba(31,20,41,0.10));
  border-radius: 12px;
  box-shadow: 0 4px 12px -8px rgba(60,20,80,0.18);
}

.stat-card h6 {
  margin: 0;
  color: var(--ink-faint, #645a72);
  font-family: var(--engraved, serif);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-size: 0.6rem;
  white-space: nowrap;
}

.stat-card span {
  font-family: var(--display, Georgia, serif);
  font-size: 1.45rem;
  line-height: 1;
  font-weight: 600;
  color: var(--tsinghua, #660874);
}
/* date reads as a date — a touch smaller but same weight/colour family */
.stat-card #last-updated { font-size: 1.05rem; }

/* Understated light table header (matches the CFP page) */
#journal-table thead th {
  background: transparent;
  color: var(--ink-strong, #100716);
  border-bottom: 2px solid rgba(102, 8, 116, 0.18);
}

.table th {
  border-top: none;
  font-weight: 600;
  font-size: 0.7rem;
  letter-spacing: 0.02em;
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
}

/* Tags styled like the CFP page */
.tag-badge {
  font-size: 0.7rem;
  margin-right: 2px;
  margin-bottom: 2px;
  display: inline-block;
}
.table th small { font-size: 0.62rem; opacity: 0.85; font-weight: 500; }

.table th:nth-child(1) { min-width: 200px; }

.table td {
  vertical-align: middle;
  font-size: 0.92rem;
}
.table td small { font-size: 0.8rem; }

/* Intro line */
.jr-intro {
  font-family: var(--display, Georgia, serif);
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--ink-soft, #4d3f5c);
  max-width: none;        /* intro spans the full content width (page width unchanged) */
  margin: 0 auto 1.6rem;
  text-align: center;
  text-wrap: pretty;
}
.jr-intro strong { color: var(--tsinghua, #660874); font-weight: 600; }
.jr-intro em { font-style: italic; color: var(--ink-strong, #100716); }

/* Column-header tooltips (bilingual via data-tip-en/zh) */
.jr-th { position: relative; }
.jr-th[data-tip-en]::after {
  position: absolute;
  left: 50%;
  top: 100%;
  transform: translateX(-50%) translateY(8px);
  white-space: normal;
  width: max-content;
  max-width: 210px;
  background: rgba(26, 22, 17, 0.95);
  color: #fff;
  font-family: var(--ui, sans-serif);
  font-size: 0.72rem;
  font-weight: 400;
  line-height: 1.45;
  letter-spacing: 0;
  text-align: left;
  text-transform: none;
  padding: 8px 11px;
  border-radius: 10px;
  box-shadow: 0 10px 28px -8px rgba(0, 0, 0, 0.5);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.18s ease, transform 0.18s ease;
  pointer-events: none;
  z-index: 50;
}
html[data-lang="en"] .jr-th[data-tip-en]::after { content: attr(data-tip-en); }
html[data-lang="zh"] .jr-th[data-tip-zh]::after { content: attr(data-tip-zh); }
.jr-th:hover::after {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(3px);
}

/* Pagination */
.jr-pagination {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 6px;
  margin-top: 18px;
}
.jr-page-btn {
  font-family: var(--ui, sans-serif);
  font-size: 0.82rem;
  min-width: 34px;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--tsinghua-pale, #d9bee0);
  background: rgba(255, 255, 255, 0.6);
  color: var(--ink-soft, #4d3f5c);
  border-radius: 9px;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}
.jr-page-btn:hover:not(:disabled) {
  border-color: var(--tsinghua, #660874);
  color: var(--tsinghua, #660874);
  transform: translateY(-1px);
}
.jr-page-btn.active {
  background: var(--tsinghua, #660874);
  color: #fff;
  border-color: var(--tsinghua, #660874);
}
.jr-page-btn:disabled { opacity: 0.4; cursor: default; }
.jr-page-ellipsis { color: var(--ink-faint, #645a72); padding: 0 4px; }

.badge-sm {
  font-size: 0.6rem;
  margin-right: 2px;
  margin-bottom: 2px;
}

@media (max-width: 768px) {
  .table-responsive {
    font-size: 0.75rem;
  }
  .search-filter-section .row > div {
    margin-bottom: 8px;
  }
}
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
  var searchInput = document.getElementById('journal-search');
  var quartileFilter = document.getElementById('quartile-filter');
  var publisherFilter = document.getElementById('publisher-filter');
  var tagFilter = document.getElementById('tag-filter');
  var tableBody = document.getElementById('journal-tbody');
  var table = document.getElementById('journal-table');
  var rows = Array.from(tableBody.querySelectorAll('tr'));
  var emptyState = document.getElementById('jr-empty-state');
  var resultsCount = document.getElementById('jr-results-count');

  // HM Score: percentile-based coloring
  function setHmScoreColors() {
    var scores = [];
    document.querySelectorAll('.hm-score').forEach(function(el) {
      var s = parseFloat(el.dataset.score);
      if (!isNaN(s)) scores.push(s);
    });
    scores.sort(function(a, b) { return a - b; });

    function getPercentile(val) {
      if (scores.length === 0) return 0;
      var idx = 0;
      for (var i = 0; i < scores.length; i++) {
        if (scores[i] <= val) idx = i;
      }
      return idx / (scores.length - 1);
    }

    document.querySelectorAll('.hm-score').forEach(function(el) {
      var score = parseFloat(el.dataset.score);
      if (isNaN(score)) return;

      var pct = getPercentile(score);
      var bgColor, textColor = 'white';
      if (pct >= 0.95) {
        bgColor = '#1a8c35';
      } else if (pct >= 0.85) {
        bgColor = '#28a745';
      } else if (pct >= 0.70) {
        bgColor = '#20c997';
      } else if (pct >= 0.55) {
        bgColor = '#17a2b8';
      } else if (pct >= 0.40) {
        bgColor = '#007bff';
      } else if (pct >= 0.25) {
        bgColor = '#6610f2';
      } else if (pct >= 0.10) {
        bgColor = '#e83e8c';
      } else {
        bgColor = '#fd7e14';
        textColor = '#212529';
      }

      el.style.backgroundColor = bgColor;
      el.style.color = textColor;
    });
  }
  setHmScoreColors();

  // Filter + pagination
  var perPage = 50;
  var currentPage = 1;
  var matched = rows.slice();

  function filterTable() {
    var searchTerm = searchInput.value.toLowerCase();
    var selectedQuartile = quartileFilter.value;
    var selectedPublisher = publisherFilter.value.toLowerCase();
    var selectedTag = tagFilter.value.toLowerCase();

    matched = rows.filter(function(row) {
      var journalName = row.dataset.journal;
      var publisher = row.dataset.publisher;
      var quartile = row.dataset.quartile;
      var tags = row.dataset.tags;
      var matchesSearch = !searchTerm || journalName.includes(searchTerm) || tags.includes(searchTerm);
      var matchesQuartile = !selectedQuartile || (quartile && quartile.includes(selectedQuartile));
      var matchesPublisher = !selectedPublisher || (publisher && publisher.includes(selectedPublisher));
      var matchesTag = !selectedTag || (tags && tags.split(',').some(function(t) { return t.trim() === selectedTag; }));
      return matchesSearch && matchesQuartile && matchesPublisher && matchesTag;
    });

    currentPage = 1;
    renderPage();
  }

  function renderPage() {
    var totalPages = Math.max(1, Math.ceil(matched.length / perPage));
    if (currentPage > totalPages) currentPage = totalPages;
    var start = (currentPage - 1) * perPage;

    rows.forEach(function(r) { r.style.display = 'none'; });
    matched.slice(start, start + perPage).forEach(function(r) { r.style.display = ''; });

    if (matched.length === 0) {
      emptyState.style.display = 'block';
      table.style.display = 'none';
    } else {
      emptyState.style.display = 'none';
      table.style.display = '';
    }

    updateStatistics();
    resultsCount.textContent = matched.length + ' / ' + rows.length;
    renderPagination(totalPages);
  }

  function renderPagination(totalPages) {
    var nav = document.getElementById('jr-pagination');
    if (!nav) return;
    nav.innerHTML = '';
    if (totalPages <= 1) return;

    function makeBtn(label, page, opts) {
      opts = opts || {};
      var b = document.createElement('button');
      b.className = 'jr-page-btn' + (opts.active ? ' active' : '');
      b.textContent = label;
      if (opts.disabled) {
        b.disabled = true;
      } else {
        b.addEventListener('click', function() {
          currentPage = page;
          renderPage();
          var anchor = document.querySelector('.search-filter-section');
          if (anchor) window.scrollTo({ top: anchor.offsetTop - 90, behavior: 'smooth' });
        });
      }
      return b;
    }

    nav.appendChild(makeBtn('‹', currentPage - 1, { disabled: currentPage === 1 }));

    var seq = [];
    for (var p = 1; p <= totalPages; p++) {
      if (p === 1 || p === totalPages || (p >= currentPage - 1 && p <= currentPage + 1)) {
        seq.push(p);
      } else if (seq[seq.length - 1] !== '...') {
        seq.push('...');
      }
    }
    seq.forEach(function(p) {
      if (p === '...') {
        var s = document.createElement('span');
        s.className = 'jr-page-ellipsis';
        s.textContent = '…';
        nav.appendChild(s);
      } else {
        nav.appendChild(makeBtn(String(p), p, { active: p === currentPage }));
      }
    });

    nav.appendChild(makeBtn('›', currentPage + 1, { disabled: currentPage === totalPages }));
  }

  function updateStatistics() {
    document.getElementById('total-journals').textContent = matched.length;
    var q1Count = matched.filter(function(r) {
      return r.dataset.quartile && r.dataset.quartile.includes('Q1');
    }).length;
    document.getElementById('q1-count').textContent = q1Count;
  }

  // Sortable table
  var currentSort = { key: 'purple', dir: 'desc' };

  function sortTable(key) {
    var dir = 'desc';
    if (currentSort.key === key && currentSort.dir === 'desc') {
      dir = 'asc';
    }
    currentSort = { key: key, dir: dir };

    // Update header styles
    document.querySelectorAll('.sortable').forEach(function(th) {
      th.classList.remove('sort-asc', 'sort-desc');
    });
    var activeTh = document.querySelector('.sortable[data-sort="' + key + '"]');
    if (activeTh) activeTh.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');

    rows.sort(function(a, b) {
      var valA, valB;

      if (key === 'name') {
        valA = a.dataset.name.toLowerCase();
        valB = b.dataset.name.toLowerCase();
        return dir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }

      // Numeric sorts
      var attrMap = {
        hm: 'hm',
        purple: 'purple',
        orange: 'orange',
        decision: 'decision',
        accept: 'accept'
      };
      valA = parseFloat(a.dataset[attrMap[key]]) || 0;
      valB = parseFloat(b.dataset[attrMap[key]]) || 0;

      // For decision time, 9999 means missing - push to bottom
      if (key === 'decision') {
        if (valA === 9999 && valB !== 9999) return 1;
        if (valB === 9999 && valA !== 9999) return -1;
      }

      if (dir === 'asc') return valA - valB;
      return valB - valA;
    });

    // Re-append in sorted order, then re-render current filter from page 1
    rows.forEach(function(row) {
      tableBody.appendChild(row);
    });
    filterTable();
  }

  document.querySelectorAll('.sortable').forEach(function(th) {
    th.addEventListener('click', function() {
      sortTable(this.dataset.sort);
    });
  });

  // Mark initial sort state
  var initialTh = document.querySelector('.sortable[data-sort="purple"]');
  if (initialTh) initialTh.classList.add('sort-desc');

  // Event listeners
  searchInput.addEventListener('input', filterTable);
  quartileFilter.addEventListener('change', filterTable);
  publisherFilter.addEventListener('change', filterTable);
  tagFilter.addEventListener('change', filterTable);

  // URL param: pre-fill search from CFP cross-link
  var urlParams = new URLSearchParams(window.location.search);
  var qParam = urlParams.get('q');
  if (qParam) {
    searchInput.value = qParam;
  }

  // Initial render — applies any ?q= param and paginates
  filterTable();

  // Initial filter
  filterTable();
});
</script>

<!-- Disclaimer -->
<div class="disclaimer mt-4">
  <small class="text-muted">
    <strong>Disclaimer:</strong> The data presented here is for reference only.
    Original metrics are linked to their respective sources.
    Please verify information from official publisher websites before making any decisions.
    <br>
    <strong>免责声明：</strong>本页面数据仅供参考，原始数据已链接至对应来源网站。请在做出任何决策前自行核实官方信息。
  </small>
</div>

{% include cfp_recommender.html %}
{% include wechat_qr.html %}
