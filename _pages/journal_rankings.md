---
layout: page
permalink: /jrank/
title: Journal Rankings
description: HM Score combines journal quality metrics and author-friendliness
nav: true
nav_order: 5
---

<div class="journal-rankings">
  <!-- Search and Filter Section -->
  <div class="search-filter-section mb-4">
    <div class="row">
      <div class="col-md-6">
        <input type="text" id="journal-search" class="form-control" placeholder="Search journals by name or tag...">
      </div>
      <div class="col-md-3">
        <select id="quartile-filter" class="form-control">
          <option value="">All Quartiles</option>
          <option value="Q1">Q1</option>
          <option value="Q2">Q2</option>
          <option value="Q3">Q3</option>
          <option value="Q4">Q4</option>
        </select>
      </div>
      <div class="col-md-3">
        <select id="publisher-filter" class="form-control">
          <option value="">All Publishers</option>
          <option value="Springer">Springer</option>
          <option value="Wiley">Wiley</option>
          <option value="Elsevier">Elsevier</option>
          <option value="Taylor">Taylor & Francis</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Journal Rankings Table -->
  <div class="table-responsive">
    <table class="table table-striped table-hover" id="journal-table">
      <thead class="thead-dark">
        <tr>
          <th>Journal Name</th>
          <th>HM</th>
          <th>Purple<br><small>(score)</small></th>
          <th>Orange<br><small>(score)</small></th>
          <th>Red</th>
          <th>Review<br><small>Timeline (Days)</small></th>
          <th>Accept<br><small>Rate</small></th>
          <th>Articles<br><small>Published</small></th>
          <th>Tags</th>
        </tr>
      </thead>
      <tbody id="journal-tbody">
        {% assign sorted_journals = site.data.jrank | sort: 'purple_score' | reverse %}
        {% for journal in sorted_journals %}
        <tr data-journal="{{ journal.journal | downcase }}" 
            data-publisher="{{ journal.publisher | downcase }}" 
            data-quartile="{{ journal.purple_quartile }}"
            data-tags="{{ journal.tag | join: ' ' | downcase }}">
          <td>
            <strong>{{ journal.journal }}</strong>
            {% if journal.publisher and journal.publisher != "" %}
              <br><small class="text-muted">{{ journal.publisher }}</small>
            {% endif %}
            {% assign journal_url = "" %}
            {% for j in site.data.journal_rank %}
              {% if j.name == journal.journal %}
                {% assign journal_url = j.url %}
              {% endif %}
            {% endfor %}
            {% if journal_url != "" %}
              <a href="{{ journal_url }}" target="_blank" class="ml-2">
                <i class="fas fa-external-link-alt"></i>
              </a>
            {% endif %}
          </td>
          <td>
            {% if journal.hm_score and journal.hm_score != "" %}
              <span class="hm-score" data-score="{{ journal.hm_score }}">
                {{ journal.hm_score }}
              </span>
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
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
          <td>
            {% if journal.orange_quartile and journal.orange_quartile != "" %}
              <span class="badge badge-orange">{{ journal.orange_quartile }}</span>
              {% if journal.orange_score and journal.orange_score != "" %}
                {% assign sourceid = "" %}
                {% for j in site.data.journal_rank %}
                  {% if j.name == journal.journal %}
                    {% assign sourceid = j.sourceid %}
                  {% endif %}
                {% endfor %}
                <br><small>
                  {% if sourceid != "" %}
                    <a href="https://www.scopus.com/sourceid/{{ sourceid }}" target="_blank">{{ journal.orange_score }}</a>
                  {% else %}
                    {{ journal.orange_score }}
                  {% endif %}
                </small>
              {% endif %}
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <td>
            {% if journal.red_division and journal.red_division != "" %}
              <span class="badge badge-red">{{ journal.red_division }}</span>
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <td>
            <small>
              {% if journal.first_decision_time and journal.first_decision_time != "" %}
                <strong>First Decision:</strong> {{ journal.first_decision_time | remove: ' days' }}<br>
              {% endif %}
              {% if journal.review_time and journal.review_time != "" %}
                <strong>Review:</strong> {{ journal.review_time | remove: ' days' }}<br>
              {% endif %}
              {% if journal.acceptance_time and journal.acceptance_time != "" %}
                <strong>To Accept:</strong> {{ journal.acceptance_time | remove: ' days' }}<br>
              {% endif %}
              {% if journal.publication_time and journal.publication_time != "" %}
                <strong>To Publish:</strong> {{ journal.publication_time | remove: ' days' }}
              {% endif %}
              {% unless journal.first_decision_time or journal.review_time or journal.acceptance_time or journal.publication_time %}
                <span class="text-muted">-</span>
              {% endunless %}
            </small>
          </td>
          <td>
            {% if journal.acceptance_rate and journal.acceptance_rate != "" %}
              {{ journal.acceptance_rate }}
            {% else %}
              <span class="text-muted">-</span>
            {% endif %}
          </td>
          <td>
            <small>
              {% if journal.documents_current_year and journal.documents_current_year != "" %}
                <strong>Current:</strong> {{ journal.documents_current_year }}<br>
              {% endif %}
              {% if journal.documents_last_year and journal.documents_last_year != "" %}
                <strong>Last Year:</strong> {{ journal.documents_last_year }}
              {% endif %}
              {% unless journal.documents_current_year or journal.documents_last_year %}
                <span class="text-muted">-</span>
              {% endunless %}
            </small>
          </td>
          <td class="tags-cell">
            {% if journal.tag %}
              {% for tag in journal.tag %}
                <span class="badge badge-secondary badge-sm">{{ tag }}</span><br>
              {% endfor %}
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Statistics Section -->
  <div class="statistics-section mt-4">
    <div class="row">
      <div class="col-md-4">
        <div class="stat-card">
          <h6>Total Journals</h6>
          <span id="total-journals">{{ site.data.jrank | size }}</span>
        </div>
      </div>
      <div class="col-md-4">
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
      <div class="col-md-4">
        <div class="stat-card">
          <h6>Last Updated</h6>
          <span id="last-updated">
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
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
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
  background-color: #6c757d; /* 默认灰色 */
}

.statistics-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.stat-card {
  text-align: center;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-card h6 {
  margin-bottom: 10px;
  color: #6c757d;
}

.stat-card span {
  font-size: 1.5rem;
  font-weight: bold;
  color: #495057;
}

.table th {
  border-top: none;
  font-weight: 600;
  font-size: 0.85rem;
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
}

/* 列宽控制 */
.table th:nth-child(1) { min-width: 200px; } /* Journal Name */
.table th:nth-child(6) { min-width: 130px; } /* Review Timeline */
.table th:nth-child(8) { min-width: 100px; } /* Articles Published */

.table td {
  vertical-align: middle;
  font-size: 0.85rem;
}

.badge-sm {
  font-size: 0.65rem;
  margin-right: 2px;
  margin-bottom: 2px;
}

@media (max-width: 768px) {
  .table-responsive {
    font-size: 0.75rem;
  }
  
  .search-filter-section .row > div {
    margin-bottom: 10px;
  }
  
  .stat-card {
    margin-bottom: 10px;
  }
}
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('journal-search');
  const quartileFilter = document.getElementById('quartile-filter');
  const publisherFilter = document.getElementById('publisher-filter');
  const tableBody = document.getElementById('journal-tbody');
  const rows = Array.from(tableBody.querySelectorAll('tr'));

  // 根据HM分数数值设置背景颜色
  function setHmScoreColors() {
    document.querySelectorAll('.hm-score').forEach(function(el) {
      const score = parseFloat(el.dataset.score);
      if (isNaN(score)) return;
      
      let bgColor, textColor = 'white';
      if (score >= 90) {
        bgColor = '#28a745';  // 绿色 - 优秀
      } else if (score >= 80) {
        bgColor = '#20c997';  // 青绿色
      } else if (score >= 70) {
        bgColor = '#17a2b8';  // 青色
      } else if (score >= 60) {
        bgColor = '#007bff';  // 蓝色
      } else if (score >= 50) {
        bgColor = '#6610f2';  // 紫色
      } else if (score >= 40) {
        bgColor = '#e83e8c';  // 粉色
      } else if (score >= 30) {
        bgColor = '#fd7e14';  // 橙色
      } else if (score >= 20) {
        bgColor = '#ffc107';  // 黄色
        textColor = '#212529';
      } else {
        bgColor = '#6c757d';  // 灰色
      }
      
      el.style.backgroundColor = bgColor;
      el.style.color = textColor;
    });
  }
  
  // 页面加载时设置颜色
  setHmScoreColors();

  function filterTable() {
    const searchTerm = searchInput.value.toLowerCase();
    const selectedQuartile = quartileFilter.value;
    const selectedPublisher = publisherFilter.value.toLowerCase();

    rows.forEach(row => {
      const journalName = row.dataset.journal;
      const publisher = row.dataset.publisher;
      const quartile = row.dataset.quartile;
      const tags = row.dataset.tags;

      const matchesSearch = journalName.includes(searchTerm) || tags.includes(searchTerm);
      const matchesQuartile = !selectedQuartile || (quartile && quartile.includes(selectedQuartile));
      const matchesPublisher = !selectedPublisher || (publisher && publisher.includes(selectedPublisher));

      if (matchesSearch && matchesQuartile && matchesPublisher) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });

    updateStatistics();
  }

  function updateStatistics() {
    const visibleRows = rows.filter(row => row.style.display !== 'none');
    document.getElementById('total-journals').textContent = visibleRows.length;
    
    const q1Count = visibleRows.filter(row => 
      row.dataset.quartile && row.dataset.quartile.includes('Q1')
    ).length;
    document.getElementById('q1-count').textContent = q1Count;
  }

  searchInput.addEventListener('input', filterTable);
  quartileFilter.addEventListener('change', filterTable);
  publisherFilter.addEventListener('change', filterTable);
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

<!-- 微信二维码浮窗 CSS -->
<style>
  .qr-float-btn {
    position: fixed;
    right: 20px;
    bottom: 100px;
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #07c160, #06ae56);
    border-radius: 50%;
    box-shadow: 0 4px 15px rgba(7, 193, 96, 0.4);
    cursor: pointer;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s, box-shadow 0.3s;
  }
  .qr-float-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(7, 193, 96, 0.5);
  }
  .qr-float-btn img {
    width: 36px;
    height: 36px;
    filter: brightness(0) invert(1);
  }
  .qr-modal-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.6);
    z-index: 1001;
    justify-content: center;
    align-items: center;
  }
  .qr-modal-overlay.active {
    display: flex;
  }
  .qr-modal-content {
    background: white;
    border-radius: 16px;
    padding: 32px;
    text-align: center;
    max-width: 400px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    animation: qrPopIn 0.3s ease;
  }
  @keyframes qrPopIn {
    from { transform: scale(0.8); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
  }
  .qr-modal-content img {
    width: 280px;
    height: 280px;
    border-radius: 12px;
    margin-bottom: 20px;
  }
  .qr-modal-content h4 {
    margin: 0 0 8px 0;
    color: #07c160;
  }
  .qr-modal-content p {
    margin: 0;
    color: #666;
    font-size: 0.9rem;
    line-height: 1.5;
  }
  .qr-close-btn {
    position: absolute;
    top: -12px;
    right: -12px;
    width: 32px;
    height: 32px;
    background: #fff;
    border: none;
    border-radius: 50%;
    font-size: 20px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }
  .qr-modal-box {
    position: relative;
  }
</style>

<!-- 微信二维码浮窗 -->
<div class="qr-float-btn" id="qrFloatBtn" title="Join WeChat Group">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="32" height="32">
    <path d="M8.5 11.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm4 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm-1.5 8c-4.14 0-7.5-2.91-7.5-6.5 0-3.59 3.36-6.5 7.5-6.5S18.5 9.41 18.5 13c0 1.38-.47 2.66-1.27 3.74l.77 2.26-2.72-.9c-1.1.57-2.35.9-3.78.9z"/>
  </svg>
</div>

<div class="qr-modal-overlay" id="qrModalOverlay">
  <div class="qr-modal-box">
    <div class="qr-modal-content">
      <button class="qr-close-btn" id="qrCloseBtn">&times;</button>
      <img src="/assets/img/wechat_qr.png" alt="WeChat QR Code">
      <h4>💬 学术交流群</h4>
      <p>
        欢迎加入学术交流群！<br>
        期刊资讯分享 · 数据问题反馈 · 新增期刊建议<br>
        <span class="text-muted" style="font-size: 0.8rem;">Join for academic discussions, data feedback & journal suggestions.</span>
      </p>
    </div>
  </div>
</div>

<script>
  // 二维码浮窗交互
  document.getElementById('qrFloatBtn').addEventListener('click', function() {
    document.getElementById('qrModalOverlay').classList.add('active');
  });
  document.getElementById('qrCloseBtn').addEventListener('click', function() {
    document.getElementById('qrModalOverlay').classList.remove('active');
  });
  document.getElementById('qrModalOverlay').addEventListener('click', function(e) {
    if (e.target === this) {
      this.classList.remove('active');
    }
  });
</script>
