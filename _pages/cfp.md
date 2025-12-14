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