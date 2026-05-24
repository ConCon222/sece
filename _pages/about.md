---
layout: about
title: About
permalink: /
subtitle: We have no reinforcements, but ourselves. | <a href='https://english.ecnu.edu.cn'>East China Normal University</a>.

profile:
  align: right
  image: photo1.jpg
  image_circular: false # crops the image to make it circular
  more_info: >
    <p>Department of Education Information Technology</p>
    <p>East China Normal University</p>
    <p>Shanghai, China</p>

selected_papers: true # includes a list of papers marked as "selected={true}"
social: true # includes social icons at the bottom of the page

announcements:
  enabled: true # includes a list of news items
  scrollable: true # adds a vertical scroll bar if there are more than 3 news items
  limit: 5 # leave blank to include all the news in the `_news` folder

latest_posts:
  enabled: true
  scrollable: true # adds a vertical scroll bar if there are more than 3 new posts items
  limit: 3 # leave blank to include all the blog posts
---

I am **Haoming Wang (王浩名)**, a researcher in the Department of Education 
Information Technology at East China Normal University. My work explores how 
artificial intelligence can meaningfully transform teaching and learning.

<div class="scholar-stats" style="display:flex; gap:24px; margin:20px 0; flex-wrap:wrap;">
  {% assign total_citations = 0 %}
  {% assign paper_cites = "" %}
  {% for paper in site.data.citations.papers %}
    {% assign total_citations = total_citations | plus: paper[1].citations %}
  {% endfor %}
  <div style="text-align:center;">
    <div style="font-size:1.8rem; font-weight:700; color:#6f42c1;">{{ site.data.citations.papers | size }}</div>
    <div style="font-size:0.75rem; color:#6c757d;">Publications</div>
  </div>
  <div style="text-align:center;">
    <div style="font-size:1.8rem; font-weight:700; color:#fd7e14;">{{ total_citations }}</div>
    <div style="font-size:0.75rem; color:#6c757d;">Citations</div>
  </div>
  <div style="text-align:center;">
    <div style="font-size:1.8rem; font-weight:700; color:#28a745;">7</div>
    <div style="font-size:0.75rem; color:#6c757d;">h-index</div>
  </div>
  <div style="text-align:center; align-self:center;">
    <a href="https://scholar.google.com/citations?user={{ site.data.socials.scholar_userid }}" target="_blank" style="font-size:0.8rem;">
      <i class="ai ai-google-scholar"></i> Google Scholar
    </a>
  </div>
</div>

## Research Interests

I focus on educational technology innovation, particularly:
- Large language models (LLMs) in education
- AI-assisted teaching and personalized learning
- Multi-agent systems for collaborative learning
- Responsible AI integration in educational contexts

## Methodology

My research employs diverse methodological approaches including quasi-experimental 
designs, lag sequential analysis, epistemic network analysis (ENA), and bibliometric 
methods to rigorously evaluate AI's impact on learning outcomes.

## Current Work

I am currently investigating AI agent empowerment in educational settings, developing 
intelligent assistants that adapt to learner needs while upholding pedagogical 
principles and ethical standards. My work bridges theoretical foundations with 
practical implementation, aiming to create solutions that are both research-informed 
and educationally impactful.

Feel free to explore my [publications](/publications/), [blog posts](/blog/), 
or reach out via email for potential collaborations on AI in education research.

I also maintain two community tools: a curated [Call for Papers](/cfp/) tracker and an [Journal Rankings](/jrank/) dashboard for education researchers.