---
layout: page
permalink: /publications/
title: Publications
title_zh: 论文发表
nav: true
nav_zh: 论文发表
nav_order: 2
---

<!-- _pages/publications.md -->
<!-- Bibsearch Feature -->
{% include bib_search.liquid %}

<div class="publication-legend" aria-label="Publication markers">
  <span class="publication-legend-item"><span class="publication-role-mark">†</span> Co-first author</span>
  <span class="publication-legend-item"><span class="publication-role-mark">*</span> Corresponding author</span>
  <span class="publication-legend-item"><i class="fa-solid fa-trophy" aria-hidden="true"></i> Highly Cited</span>
  <span class="publication-legend-item"><i class="fa-solid fa-fire" aria-hidden="true"></i> Hot Paper</span>
</div>

{%- comment -%}
  1. 先把 Journal / Conference 的 bibliography 渲染到临时变量里
{%- endcomment -%}
{%- capture journal_html -%}
  {% bibliography -q @article %}
{%- endcapture -%}

{%- capture conf_html -%}
  {% bibliography -q @inproceedings %}
{%- endcapture -%}

{%- comment -%}
  2. 通过数 <li> 的个数来估计条目数
     注意：split:'<li' 结果会比实际条目数多 1（开头空串），所以要减 1
{%- endcomment -%}
{%- assign journal_count = journal_html | split:'<li' | size | minus: 1 -%}
{%- assign conf_count    = conf_html    | split:'<li' | size | minus: 1 -%}

<div class="publications">
<h2>Journal Papers ({{ journal_count }})</h2>
  {% bibliography -q @article %}

<h2>Conference Papers ({{ conf_count }})</h2>
  {% bibliography -q @inproceedings %}
</div>
