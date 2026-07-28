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
{% assign jr_publishers = site.data.jrank | map: 'publisher' | compact | uniq | sort %}
{% assign jr_publisher_count = 0 %}
{% for publisher in jr_publishers %}
  {% assign publisher_name = publisher | strip %}
  {% if publisher_name != "" %}{% assign jr_publisher_count = jr_publisher_count | plus: 1 %}{% endif %}
{% endfor %}
{% assign jr_last_updated = site.data.jrank_meta.last_successful_update | default: site.data.jrank_meta.last_updated %}

<div class="journal-rankings">
  {% include context_rail.liquid items="jr-overview::Overview::概览|jr-filters::Filters::筛选|jr-results::Rankings::排名|jr-notes::Notes::说明" %}
  <section id="jr-overview" class="context-rail-target">
  <!-- What this is -->
  <p class="jr-intro">
    <span class="only-en">A curated dashboard of education &amp; related-field journals, ranked by an <strong>HM friendliness score</strong> that combines JCR quartile and Impact Factor, CiteScore and percentile, acceptance rate, and recent article volume, so you can quickly compare potential submission venues.</span>
    <span class="only-zh">教育及相关领域期刊的精选看板，按 <strong>HM 友好性指数</strong> 排名——该指数综合 JCR 分区与影响因子、CiteScore 与百分位、录用率及近期发文量，便于快速比较潜在投稿目标。</span>
  </p>

  <!-- At-a-glance statistics -->
  <div class="statistics-section mb-4">
    <div class="row">
      <div class="col-6 col-md-3"><div class="stat-card"><h6><span class="only-en">Total Journals</span><span class="only-zh">期刊总数</span></h6><span id="total-journals">{{ site.data.jrank | size }}</span></div></div>
      <div class="col-6 col-md-3"><div class="stat-card"><h6><span class="only-en">Q1 Journals</span><span class="only-zh">Q1 期刊</span></h6><span id="q1-count">{% assign q1_count = 0 %}{% for journal in site.data.jrank %}{% if journal.purple_quartile contains 'Q1' %}{% assign q1_count = q1_count | plus: 1 %}{% endif %}{% endfor %}{{ q1_count }}</span></div></div>
      <div class="col-6 col-md-3"><div class="stat-card"><h6><span class="only-en">Publishers</span><span class="only-zh">出版商</span></h6><span>{{ jr_publisher_count }}</span></div></div>
      <div class="col-6 col-md-3"><div class="stat-card"><h6><span class="only-en">Last Updated</span><span class="only-zh">最近更新</span></h6><span id="last-updated">{% if jr_last_updated %}{{ jr_last_updated | date: "%Y-%m-%d" }}{% else %}—{% endif %}</span></div></div>
    </div>
  </div>
  </section>

  <!-- Search and Filter Section -->
  <div class="search-filter-section mb-4 context-rail-target" id="jr-filters">
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
          {% for p in jr_publishers %}{% if p != "" %}<option value="{{ p }}">{{ p }}</option>{% endif %}{% endfor %}
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
  <div id="jr-results" class="context-rail-target">
  <div class="table-responsive">
    <table class="table table-striped table-hover" id="journal-table" data-source="{{ '/assets/data/jrank-browser.json' | relative_url }}">
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
      <tbody id="journal-tbody"><tr><td colspan="9">Loading journal rankings…</td></tr></tbody>
    </table>
  </div>

  <!-- Pagination controls -->
  <nav class="jr-pagination" id="jr-pagination" aria-label="Journal table pages"></nav>

  <!-- Empty state -->
  <div class="jr-empty-state" id="jr-empty-state" style="display:none;">
    <p><span class="only-en">No matching journals found.<br>Try adjusting your filters.</span><span class="only-zh">没有匹配的期刊。<br>试试调整筛选条件。</span></p>
  </div>
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
/* English labels run wider (TOTAL JOURNALS / LAST UPDATED) — one notch smaller */
html[data-lang="en"] .stat-card h6 { font-size: 0.53rem; }

.stat-card > span {
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
  .statistics-section { padding: 12px; }
  .statistics-section .row > div { margin-bottom: 10px; }
  .stat-card { min-width: 0; padding: 12px 6px; }
  .stat-card h6 { white-space: normal; line-height: 1.25; }
  .search-filter-section .row > div {
    margin-bottom: 8px;
  }
  #journal-table,
  #journal-table tbody { display: block; width: 100%; }
  #journal-table thead { display: none; }
  #journal-table tbody tr {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0;
    padding: 16px;
    border-bottom: 1px solid rgba(102, 8, 116, 0.12);
  }
  #journal-table tbody tr:last-child { border-bottom: 0; }
  #journal-table tbody td {
    display: block;
    width: 100%;
    min-width: 0;
    padding: 9px 6px;
    border: 0;
    text-align: left;
    font-size: 0.9rem;
  }
  #journal-table tbody td[data-label="Journal"],
  #journal-table tbody td[data-label="More"],
  #journal-table tbody td[data-label="Tags"] { grid-column: 1 / -1; }
  #journal-table tbody td[data-label="Journal"] {
    padding-top: 0;
    padding-bottom: 13px;
    border-bottom: 1px solid rgba(31, 20, 41, 0.08);
  }
  .jr-journal-name { font-family: var(--display, Georgia, serif); font-size: 1.08rem; line-height: 1.3; }
  .jr-mobile-label {
    display: block;
    margin-bottom: 5px;
    font-family: var(--ui, sans-serif);
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    color: var(--ink-faint, #645a72);
    text-transform: uppercase;
  }
  .jr-details-box { white-space: normal; }
  .jr-page-btn { min-width: 38px; height: 38px; }
}
@media (min-width: 769px) { .jr-mobile-label { display: none; } }

.jr-external-link { margin-left: 4px; font-family: var(--ui, sans-serif); }
.jr-details summary { cursor: pointer; white-space: nowrap; color: var(--tsinghua, #660874); font-family: var(--ui, sans-serif); font-size: 0.8rem; }
</style>

<script defer src="{{ '/assets/js/journal-rankings.js' | relative_url | bust_file_cache }}"></script>

<!-- Disclaimer -->
<div class="disclaimer mt-4 context-rail-target" id="jr-notes">
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
