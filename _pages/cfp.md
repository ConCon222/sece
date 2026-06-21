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
{% assign sorted_cfps = site.data.cfps | sort: 'fullpaper_deadline_sort' %}

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
    .table-responsive { font-size: 0.78rem; }
    .cfp-filter-section { padding: 12px; }
  }
</style>

<!-- Search & Filter Section -->
<div class="cfp-filter-section">
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

<div class="results-count" id="cfp-results-count"></div>

<div class="table-responsive">
  <table class="table table-hover" id="cfp-table">
    <thead>
      <tr>
        <th width="18%" class="cfp-sortable" data-sort="deadline">Deadline <span class="cfp-sort-icon"></span></th>
        <th width="15%" class="cfp-sortable" data-sort="journal">Journal <span class="cfp-sort-icon"></span></th>
        <th width="55%">Topic &amp; Details</th>
        <th width="12%">Tags</th>
      </tr>
    </thead>
    <tbody id="cfp-table-body">
      {% for cfp in sorted_cfps %}
      {% assign today_date = 'now' | date: '%Y-%m-%d' %}
      {% assign is_expired = false %}
      {% if cfp.fullpaper_deadline_sort < today_date and cfp.fullpaper_deadline_sort != '9999-99-99' %}
        {% assign is_expired = true %}
      {% endif %}

      <tr class="cfp-row{% if is_expired %} cfp-expired{% endif %}"
          data-tags="{{ cfp.tag | join: ',' }}"
          data-journal="{{ cfp.journal | downcase | xml_escape }}"
          data-title="{{ cfp.title | downcase | xml_escape }}"
          data-publisher="{{ cfp.publisher | downcase | xml_escape }}"
          data-deadline="{{ cfp.fullpaper_deadline_sort }}"
          data-expired="{{ is_expired }}">

        <td>
          {% if is_expired %}
            <span class="badge deadline-expired">Expired</span>
          {% elsif cfp.fullpaper_deadline_sort == '9999-99-99' %}
            <span class="badge deadline-tba">TBA</span>
          {% else %}
            <span class="badge deadline-active">{{ cfp.fullpaper_deadline_sort }}</span>
            <div class="countdown-text" data-deadline="{{ cfp.fullpaper_deadline_sort }}"></div>
          {% endif %}
          <div class="small text-muted mt-1">
            {{ cfp.fullpaper_deadline | default: "See Website" }}
          </div>
        </td>

        <td>
          <div style="line-height: 1.2;">
            <b>{{ cfp.journal }}</b>
            <a href="/jrank/?q={{ cfp.journal | url_encode }}" class="cfp-journal-link" title="View journal metrics">IF/HM</a>
            <div class="small text-muted mt-1"><i>{{ cfp.publisher }}</i></div>
          </div>
        </td>

        <td>
          {% assign scope = cfp.description | strip_html | strip %}
          {% assign has_more = false %}
          {% if scope != "" and scope != "N/A" %}{% assign has_more = true %}{% endif %}
          {% if cfp.abstract_deadline != "" and cfp.abstract_deadline != nil %}{% assign has_more = true %}{% endif %}
          {% if cfp.editors != "" and cfp.editors != "N/A" %}{% assign has_more = true %}{% endif %}

          <a href="{{ cfp.link }}" target="_blank" rel="noopener" class="cfp-title">{{ cfp.title }}</a>

          {% if scope != "" and scope != "N/A" %}
            <p class="cfp-scope">{{ scope | truncate: 150 }}</p>
          {% endif %}

          <div class="cfp-row-actions">
            <a href="{{ cfp.link }}" target="_blank" rel="noopener" class="cfp-cta">
              <span class="only-en">View call &amp; submit&nbsp;↗</span><span class="only-zh">查看征稿并投稿&nbsp;↗</span>
            </a>
            {% if has_more %}
            <details class="cfp-more">
              <summary><span class="only-en">More</span><span class="only-zh">更多</span></summary>
              <div class="cfp-details-box">
                {% if cfp.abstract_deadline != "" and cfp.abstract_deadline != nil %}
                <div class="mb-2"><span class="cfp-meta-label"><span class="only-en">Abstract deadline:</span><span class="only-zh">摘要截止：</span></span> {{ cfp.abstract_deadline }}</div>
                {% endif %}
                {% if cfp.editors != "" and cfp.editors != "N/A" %}
                <div class="mb-2"><span class="cfp-meta-label"><span class="only-en">Guest editors:</span><span class="only-zh">特邀编辑：</span></span> {{ cfp.editors }}</div>
                {% endif %}
                {% if scope != "" and scope != "N/A" %}
                <div class="mt-2">
                  <span class="cfp-meta-label"><span class="only-en">Scope:</span><span class="only-zh">征稿范围：</span></span>
                  <p class="mb-0 text-muted" style="white-space: pre-wrap;">{{ scope | truncate: 400 }}</p>
                </div>
                {% endif %}
              </div>
            </details>
            {% endif %}
          </div>
        </td>

        <td>
          {% for t in cfp.tag %}
            <span class="badge badge-light border tag-badge">{{ t }}</span>
          {% endfor %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<!-- Empty state -->
<div class="cfp-empty-state" id="cfp-empty-state">
  <p>No matching Call for Papers found.<br>Try adjusting your filters.</p>
</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
  var searchInput = document.getElementById('cfp-search');
  var tagFilter = document.getElementById('cfp-tag-filter');
  var publisherFilter = document.getElementById('cfp-publisher-filter');
  var showExpiredToggle = document.getElementById('cfp-show-expired');
  var rows = Array.from(document.querySelectorAll('.cfp-row'));
  var emptyState = document.getElementById('cfp-empty-state');
  var resultsCount = document.getElementById('cfp-results-count');
  var table = document.getElementById('cfp-table');

  // Calculate and display countdown
  function setCountdowns() {
    document.querySelectorAll('.countdown-text[data-deadline]').forEach(function(el) {
      var deadline = new Date(el.dataset.deadline + 'T23:59:59');
      var now = new Date();
      var diffDays = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
      if (diffDays < 0) return;
      el.textContent = diffDays + ' day' + (diffDays !== 1 ? 's' : '') + ' left';
      if (diffDays > 30) {
        el.classList.add('comfortable');
      } else {
        el.classList.remove('comfortable');
      }
      // Urgent coloring for deadline badge (<=14 days)
      if (diffDays <= 14) {
        var badge = el.parentElement.querySelector('.deadline-active');
        if (badge) {
          badge.classList.remove('deadline-active');
          badge.classList.add('deadline-urgent');
        }
      }
    });
  }
  setCountdowns();

  // Combined filter logic
  function filterTable() {
    var searchTerm = searchInput.value.toLowerCase();
    var selectedTag = tagFilter.value;
    var selectedPublisher = publisherFilter.value.toLowerCase();
    var showExpired = showExpiredToggle.checked;

    var visibleCount = 0;

    rows.forEach(function(row) {
      var isExpired = row.dataset.expired === 'true';
      var journal = row.dataset.journal;
      var title = row.dataset.title;
      var publisher = row.dataset.publisher;
      var rawTags = row.dataset.tags;
      var rowTags = rawTags ? rawTags.split(',') : [];

      // Expired filter
      if (isExpired && !showExpired) {
        row.style.display = 'none';
        return;
      }

      // Search
      var matchesSearch = !searchTerm ||
        journal.includes(searchTerm) ||
        title.includes(searchTerm) ||
        rawTags.toLowerCase().includes(searchTerm);

      // Tag filter
      var matchesTag = !selectedTag || rowTags.includes(selectedTag);

      // Publisher filter
      var matchesPublisher = !selectedPublisher || publisher.includes(selectedPublisher);

      if (matchesSearch && matchesTag && matchesPublisher) {
        row.style.display = '';
        visibleCount++;
      } else {
        row.style.display = 'none';
      }
    });

    // Empty state
    if (visibleCount === 0) {
      emptyState.style.display = 'block';
      table.style.display = 'none';
    } else {
      emptyState.style.display = 'none';
      table.style.display = '';
    }

    // Results count
    var totalActive = rows.filter(function(r) { return r.dataset.expired !== 'true'; }).length;
    if (searchTerm || selectedTag || selectedPublisher || showExpired) {
      resultsCount.textContent = 'Showing ' + visibleCount + ' of ' + rows.length + ' entries';
    } else {
      resultsCount.textContent = totalActive + ' active calls for papers';
    }
  }

  searchInput.addEventListener('input', filterTable);
  tagFilter.addEventListener('change', filterTable);
  publisherFilter.addEventListener('change', filterTable);
  showExpiredToggle.addEventListener('change', filterTable);

  // Sortable columns (Deadline / Journal)
  var cfpSort = { key: 'deadline', dir: 'asc' };
  function sortCfp(key) {
    var dir = (cfpSort.key === key && cfpSort.dir === 'asc') ? 'desc' : 'asc';
    cfpSort = { key: key, dir: dir };
    document.querySelectorAll('.cfp-sortable').forEach(function(th) { th.classList.remove('sort-asc', 'sort-desc'); });
    var activeTh = document.querySelector('.cfp-sortable[data-sort="' + key + '"]');
    if (activeTh) activeTh.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');
    rows.sort(function(a, b) {
      var va, vb;
      if (key === 'journal') {
        va = a.dataset.journal; vb = b.dataset.journal;
        return dir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
      }
      va = a.dataset.deadline || '9999-99-99';
      vb = b.dataset.deadline || '9999-99-99';
      if (va < vb) return dir === 'asc' ? -1 : 1;
      if (va > vb) return dir === 'asc' ? 1 : -1;
      return 0;
    });
    var tbody = document.getElementById('cfp-table-body');
    rows.forEach(function(r) { tbody.appendChild(r); });
    filterTable();
  }
  document.querySelectorAll('.cfp-sortable').forEach(function(th) {
    th.addEventListener('click', function() { sortCfp(this.dataset.sort); });
  });
  var initCfpTh = document.querySelector('.cfp-sortable[data-sort="deadline"]');
  if (initCfpTh) initCfpTh.classList.add('sort-asc');

  // URL param: pre-fill search from Journal Rankings cross-link
  var urlParams = new URLSearchParams(window.location.search);
  var qParam = urlParams.get('q');
  if (qParam) {
    searchInput.value = qParam;
  }

  // Initial filter (hide expired by default)
  filterTable();
});
</script>

<hr class="mt-5 mb-3">
<p class="text-muted small text-center">
  <em>Disclaimer: The information on this page is for reference only. Deadlines and details may change. Please visit the official links to verify the latest information.</em><br>
  <em>免责声明：本页面信息仅供参考，截止日期可能有变动，请访问原链接确认最新信息，一切以官方网站为准。</em>
</p>

{% include cfp_recommender.html %}
{% include wechat_qr.html %}
