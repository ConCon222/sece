---
layout: page
permalink: /jrank/
title: Journal Rankings
description: HM Score combines journal quality metrics and author-friendliness
nav: true
nav_order: 5
---

{% assign all_tags = site.data.jrank | map: 'tag' | join: ',' | split: ',' | uniq | sort %}

<div class="journal-rankings">
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
      <thead class="thead-dark">
        <tr>
          <th class="sortable" data-sort="name">Journal Name <span class="sort-icon"></span></th>
          <th class="sortable" data-sort="hm">HM <span class="sort-icon"></span></th>
          <th class="sortable" data-sort="purple">Purple<br><small>(IF)</small> <span class="sort-icon"></span></th>
          <th class="sortable" data-sort="orange">Orange<br><small>(CiteScore)</small> <span class="sort-icon"></span></th>
          <th>Red</th>
          <th class="sortable" data-sort="decision">First<br><small>Decision</small> <span class="sort-icon"></span></th>
          <th class="sortable" data-sort="accept">Accept<br><small>Rate</small> <span class="sort-icon"></span></th>
          <th>More</th>
          <th>Tags</th>
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
                <span class="badge badge-secondary badge-sm">{{ tag }}</span>
              {% endfor %}
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Empty state -->
  <div class="jr-empty-state" id="jr-empty-state" style="display:none;">
    <p>No matching journals found.<br>Try adjusting your filters.</p>
  </div>

  <!-- Statistics Section -->
  <div class="statistics-section mt-4">
    <div class="row">
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <h6>Total Journals</h6>
          <span id="total-journals">{{ site.data.jrank | size }}</span>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <h6>Q1 Journals</h6>
          <span id="q1-count">
            {% assign q1_count = 0 %}
            {% for journal in site.data.jrank %}
              {% if journal.purple_quartile contains 'Q1' %}
                {% assign q1_count = q1_count | plus: 1 %}
              {% endif %}
            {% endfor %}
            {{ q1_count }}
          </span>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <h6>Publishers</h6>
          <span>5</span>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <h6>Last Updated</h6>
          <span id="last-updated" style="font-size:1rem;">
            {{ site.time | date: "%Y-%m-%d" }}
          </span>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
.journal-rankings {
  padding: 20px 0;
}

.search-filter-section {
  background: #f8f9fa;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
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
  background-color: #6f42c1;
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
}
.sortable:hover {
  background-color: rgba(255,255,255,0.1);
}
.sort-icon {
  font-size: 0.65rem;
  margin-left: 2px;
  opacity: 0.5;
}
.sort-icon::after {
  content: '⇅';
}
.sortable.sort-asc .sort-icon::after {
  content: '↑';
  opacity: 1;
}
.sortable.sort-desc .sort-icon::after {
  content: '↓';
  opacity: 1;
}
.sortable.sort-asc .sort-icon,
.sortable.sort-desc .sort-icon {
  opacity: 1;
}

/* Cross-link to CFP */
.jr-cfp-link {
  font-size: 0.65rem;
  color: #17a2b8;
  text-decoration: none;
  margin-left: 4px;
  border: 1px solid #17a2b8;
  padding: 0 3px;
  border-radius: 3px;
}
.jr-cfp-link:hover {
  background-color: #17a2b8;
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
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 8px;
}

.stat-card h6 {
  margin-bottom: 8px;
  color: #6c757d;
  font-size: 0.8rem;
}

.stat-card span {
  font-size: 1.3rem;
  font-weight: bold;
  color: #495057;
}

.table th {
  border-top: none;
  font-weight: 600;
  font-size: 0.8rem;
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
}

.table th:nth-child(1) { min-width: 200px; }

.table td {
  vertical-align: middle;
  font-size: 0.83rem;
}

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

  // Filter logic
  function filterTable() {
    var searchTerm = searchInput.value.toLowerCase();
    var selectedQuartile = quartileFilter.value;
    var selectedPublisher = publisherFilter.value.toLowerCase();
    var selectedTag = tagFilter.value.toLowerCase();

    var visibleCount = 0;

    rows.forEach(function(row) {
      var journalName = row.dataset.journal;
      var publisher = row.dataset.publisher;
      var quartile = row.dataset.quartile;
      var tags = row.dataset.tags;

      var matchesSearch = !searchTerm || journalName.includes(searchTerm) || tags.includes(searchTerm);
      var matchesQuartile = !selectedQuartile || (quartile && quartile.includes(selectedQuartile));
      var matchesPublisher = !selectedPublisher || (publisher && publisher.includes(selectedPublisher));
      var matchesTag = !selectedTag || (tags && tags.split(',').some(function(t) { return t.trim() === selectedTag; }));

      if (matchesSearch && matchesQuartile && matchesPublisher && matchesTag) {
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

    updateStatistics();
    resultsCount.textContent = visibleCount + ' / ' + rows.length;
  }

  function updateStatistics() {
    var visibleRows = rows.filter(function(r) { return r.style.display !== 'none'; });
    document.getElementById('total-journals').textContent = visibleRows.length;

    var q1Count = visibleRows.filter(function(r) {
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

    // Re-append sorted rows
    rows.forEach(function(row) {
      tableBody.appendChild(row);
    });
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

{% include wechat_qr.html %}
