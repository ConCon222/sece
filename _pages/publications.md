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
{% include context_rail.liquid items="publication-search::Search::检索|journal-papers::Journals::期刊论文|conference-papers::Conferences::会议论文" %}
<div id="publication-search" class="context-rail-target">
{% include bib_search.liquid %}
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
<section id="journal-papers" class="context-rail-target">
<h2>Journal Papers ({{ journal_count }})</h2>
  {% bibliography -q @article %}
</section>

<section id="conference-papers" class="context-rail-target">
<h2>Conference Papers ({{ conf_count }})</h2>
  {% bibliography -q @inproceedings %}
</section>
</div>
