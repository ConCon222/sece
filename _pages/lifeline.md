---
layout: page
permalink: /lifeline/
title: lifeline
description: my lifeline
nav: false
nav_order: 5
---


{% for year_group in site.data.lifeline %}
  <h2>{{ year_group.year }}</h2>
  {% for award in year_group.items %}
    <div class="award-item">
      <h3>{{ award.title }}</h3>
      <p>{{ award.organization }}</p>
    </div>
  {% endfor %}
{% endfor %}