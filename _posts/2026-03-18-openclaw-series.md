---
layout: distill
title: "OpenClaw × ECNU AI: Setup Series Overview"
title_zh: "OpenClaw × ECNU AI：配置系列总览"
date: 2026-03-18
description: "A guide to the three OpenClaw setup posts: retrieving API credentials, completing the local installation, and connecting a Feishu bot."
description_zh: "三篇 OpenClaw 配置教程导览：获取 API 凭证、完成本地安装、连接飞书机器人。"
tags: [OpenClaw, ECNU AI]
categories: tutorial
thumbnail: assets/img/posts/openclaw-tutorial/install-step0.png
giscus_comments: true
featured: true

authors:
  - name: Haoming Wang
    url: "https://frank-haoming.github.io/"

toc:
  - name: Series Overview
  - name: Reading Order
  - name: "What You Gain from the Series"

_styles: >
  .series-hero {
    background: linear-gradient(135deg, #7d1a8c 0%, #4a0a5e 100%);
    color: white;
    padding: 2rem;
    border-radius: 18px;
    margin: 1.5rem 0 2rem;
  }
  .series-hero p:last-child {
    margin-bottom: 0;
  }
  .series-note {
    background: #f6f8fb;
    border: 1px solid #d8e1eb;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin: 1.5rem 0;
  }
  .series-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1.25rem;
    margin: 1.5rem 0 2rem;
  }
  .series-card {
    background: white;
    border: 1px solid #d9bee0;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 14px 30px rgba(16, 35, 52, 0.08);
  }
  .series-card img {
    display: block;
    width: 100%;
    aspect-ratio: 16 / 10;
    object-fit: cover;
    background: #eef3f7;
  }
  .series-card-body {
    padding: 1.2rem 1.2rem 1.35rem;
  }
  .series-step {
    display: inline-block;
    margin-bottom: 0.7rem;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    background: #eaf2ff;
    color: #660874;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.02em;
  }
  .series-card h3 {
    margin: 0 0 0.55rem;
    font-size: 1.18rem;
    line-height: 1.35;
  }
  .series-card p {
    margin-bottom: 0.8rem;
  }
  .series-meta {
    color: #4d3f5c;
    font-size: 0.92rem;
  }
  .series-link {
    display: inline-block;
    margin-top: 0.45rem;
    font-weight: 700;
  }
  .series-outcomes {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.9rem;
    margin: 1.5rem 0;
  }
  .series-outcome {
    background: linear-gradient(180deg, #faf8fc 0%, #f1e6f5 100%);
    border: 1px solid #d9bee0;
    border-radius: 14px;
    padding: 1rem 1.1rem;
  }
---

## Series Overview

This set of posts follows a continuous setup path: first retrieve API credentials from ChatECNU, then complete the OpenClaw installation locally, and finally extend the same model setup into a Feishu bot. Each post can be read on its own, but the order is clear enough that it is useful to provide a single entry point for the full sequence.

<div class="series-hero">
  <p><strong>Who this series is for:</strong> Readers who want to connect OpenClaw to the ECNU AI platform and then extend the same setup into Feishu.</p>
  <p><strong>How to read it:</strong> If you are setting everything up for the first time, follow the order ① → ② → ③. If you only need one specific part, jump directly to the relevant post.</p>
</div>

<div class="series-note">
  <strong>What this page does:</strong> It does not compress the three tutorials into one long article. Instead, it serves as a single entry point that clarifies the setup path, the target reader, and the recommended reading order.
</div>

## Reading Order

<div class="series-grid">
  <article class="series-card">
    <img src="{{ '/assets/img/posts/openclaw-tutorial/api-step0.png' | relative_url }}" alt="Tutorial one cover">
    <div class="series-card-body">
      <span class="series-step">Step 1</span>
      <h3>Retrieve ECNU AI API Credentials</h3>
      <p>Collect the API key, base URL, and model name from ChatECNU before starting the OpenClaw setup.</p>
      <p class="series-meta">Best for readers who have not yet organized their API parameters.</p>
      <a class="series-link" href="/blog/2026/openclaw-tutorial-1/">Read Tutorial I</a>
    </div>
  </article>

  <article class="series-card">
    <img src="{{ '/assets/img/posts/openclaw-tutorial/install-step0.png' | relative_url }}" alt="Tutorial two cover">
    <div class="series-card-body">
      <span class="series-step">Step 2</span>
      <h3>Install OpenClaw and Connect ECNU AI</h3>
      <p>Complete the local installation, choose the provider, enter the API values, and verify that the setup works.</p>
      <p class="series-meta">Best for readers who want a working local environment as quickly as possible.</p>
      <a class="series-link" href="/blog/2026/openclaw-tutorial-2/">Read Tutorial II</a>
    </div>
  </article>

  <article class="series-card">
    <img src="{{ '/assets/img/posts/openclaw-tutorial/feishu-step13.png' | relative_url }}" alt="Tutorial three cover">
    <div class="series-card-body">
      <span class="series-step">Step 3</span>
      <h3>Connect a Feishu Bot</h3>
      <p>Create the app on the Feishu Open Platform, import permissions, subscribe to events, and publish the integration.</p>
      <p class="series-meta">Best for readers who have already completed the local setup and want to expand into Feishu.</p>
      <a class="series-link" href="/blog/2026/openclaw-tutorial-3/">Read Tutorial III</a>
    </div>
  </article>
</div>

## What You Gain from the Series

<div class="series-outcomes">
  <div class="series-outcome">
    <strong>A reusable set of API credentials</strong><br/>
    You no longer need to reconstruct the required endpoint values from memory every time.
  </div>
  <div class="series-outcome">
    <strong>A working OpenClaw environment in the terminal</strong><br/>
    You can call the ECNU AI model directly from the local interface.
  </div>
  <div class="series-outcome">
    <strong>A clear path from local setup to Feishu</strong><br/>
    The same model endpoint can support both the terminal workflow and the Feishu bot workflow.
  </div>
</div>

If you only want to complete one part of the setup, this overview works as a quick entry point. If you plan to walk through the entire process, it also helps you see where you are and what to read next.
