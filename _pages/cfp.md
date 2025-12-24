---
layout: page
title: Call for Papers
permalink: /cfp/
description: Curated academic opportunities in Edu. Auto-updated daily.
nav: true
nav_order: 3
---

{% assign all_tags = site.data.cfps | map: 'tag' | join: ',' | split: ',' | uniq | sort %}

<style>
  .filter-btn {
    margin-right: 5px;
    margin-bottom: 5px;
    border-radius: 20px;
    font-size: 0.85rem;
    text-transform: capitalize;
  }
  .filter-btn.active {
    background-color: #007bff;
    color: white;
    border-color: #007bff;
  }
  .cfp-details-box {
    background-color: #f8f9fa;
    border-left: 3px solid #17a2b8;
    padding: 10px 15px;
    margin-top: 10px;
    border-radius: 0 5px 5px 0;
    font-size: 0.9rem;
  }
  .cfp-meta-label {
    font-weight: 600;
    color: #495057;
  }
  /* 新增：标签小徽章的样式 */
  .tag-badge {
    font-size: 0.75rem;
    margin-right: 2px;
    margin-bottom: 2px;
    display: inline-block;
  }
  /* 微信二维码浮窗 */
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

<div class="mb-4">
  <div id="tag-filters">
    <button class="btn btn-sm btn-outline-primary filter-btn active" data-filter="all">All</button>
    {% for tag in all_tags %}
      {% if tag != "" %}
      <button class="btn btn-sm btn-outline-secondary filter-btn" data-filter="{{ tag | strip }}">{{ tag | strip }}</button>
      {% endif %}
    {% endfor %}
  </div>
</div>

<div class="table-responsive">
  <table class="table table-hover">
    <thead>
      <tr>
        <th width="15%">Deadline</th>
        <th width="15%">Journal</th>
        <th width="60%">Topic & Details</th>
        <th width="10%">Tags</th> </tr>
    </thead>
    <tbody id="cfp-table-body">
      {% for cfp in site.data.cfps %}
      
      <tr class="cfp-row" data-tags="{{ cfp.tag | join: ',' }}">
        
        <td>
          {% assign today_date = 'now' | date: '%Y-%m-%d' %}
          {% if cfp.fullpaper_deadline_sort < today_date and cfp.fullpaper_deadline_sort != '9999-99-99' %}
            <span class="badge badge-secondary">Expired</span>
          {% elsif cfp.fullpaper_deadline_sort == '9999-99-99' %}
            <span class="badge badge-warning text-dark">TBA</span>
          {% else %}
            <span class="badge badge-success">{{ cfp.fullpaper_deadline_sort }}</span>
          {% endif %}
          <div class="small text-muted mt-1">
            {{ cfp.fullpaper_deadline | default: "See Website" }}
          </div>
        </td>
        
        <td>
          <div style="line-height: 1.2;">
            <b>{{ cfp.journal }}</b>
            <div class="small text-muted mt-1"><i>{{ cfp.publisher }}</i></div>
          </div>
        </td>
        
        <td>
          <a href="{{ cfp.link }}" target="_blank" style="font-weight: 600;">{{ cfp.title }}</a>
          
          <details class="mt-2">
            <summary class="small text-primary" style="cursor: pointer;">Show Details</summary>
            <div class="cfp-details-box">
              {% if cfp.abstract_deadline != "" and cfp.abstract_deadline != nil %}
              <div class="mb-2"><span class="cfp-meta-label">📝 Abstract Deadline:</span> {{ cfp.abstract_deadline }}</div>
              {% endif %}
              {% if cfp.editors != "" and cfp.editors != "N/A" %}
              <div class="mb-2"><span class="cfp-meta-label">👥 Editors:</span> {{ cfp.editors }}</div>
              {% endif %}
              {% if cfp.description != "" and cfp.description != "N/A" %}
              <div class="mt-2">
                <span class="cfp-meta-label">ℹ️ Description:</span>
                <p class="mb-0 text-muted" style="white-space: pre-wrap;">{{ cfp.description | strip_html | truncate: 350 }}</p>
              </div>
              {% endif %}
              <div class="mt-2"><a href="{{ cfp.link }}" target="_blank" class="btn btn-sm btn-light border">Visit Website &rarr;</a></div>
            </div>
          </details>
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

<script>
document.addEventListener("DOMContentLoaded", function() {
  const filterButtons = document.querySelectorAll('.filter-btn');
  const rows = document.querySelectorAll('.cfp-row');

  filterButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      // 1. 按钮样式切换
      filterButtons.forEach(b => {
        b.classList.remove('active', 'btn-outline-primary');
        b.classList.add('btn-outline-secondary');
      });
      this.classList.remove('btn-outline-secondary');
      this.classList.add('active', 'btn-outline-primary');

      const filterValue = this.getAttribute('data-filter');

      // 2. 筛选逻辑升级：使用 split + includes
      rows.forEach(row => {
        // 获取该行的所有 tag，分割成数组
        // data-tags="edu tech,higher ed" -> ['edu tech', 'higher ed']
        const rawTags = row.getAttribute('data-tags');
        const rowTags = rawTags ? rawTags.split(',') : [];

        if (filterValue === 'all') {
          row.style.display = '';
        } else {
          // 检查数组中是否包含选中的 tag
          if (rowTags.includes(filterValue)) {
             row.style.display = '';
          } else {
             row.style.display = 'none';
          }
        }
      });
    });
  });
});
</script>

<hr class="mt-5 mb-3">
<p class="text-muted small text-center">
  <em>⚠️ Disclaimer: The information on this page is for reference only. Deadlines and details may change. Please visit the official links to verify the latest information.</em><br>
  <em>⚠️ 免责声明：本页面信息仅供参考，截止日期可能有变动，请访问原链接确认最新信息，一切以官方网站为准。</em>
</p>

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