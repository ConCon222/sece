---
layout: distill
title: "OpenClaw Setup (I): Retrieve ECNU AI API Credentials"
title_zh: "OpenClaw 配置（一）：获取 ECNU AI API 凭证"
date: 2026-03-12
description: Retrieve the API key, base URL, and model name from ChatECNU before connecting OpenClaw.
description_zh: 在连接 OpenClaw 之前，从 ChatECNU 获取 API 密钥、Base URL 与模型名称。
tags: [OpenClaw, ECNU AI, API]
categories: tutorial
thumbnail: assets/img/posts/openclaw-tutorial/api-step0.png
giscus_comments: true
featured: false

authors:
  - name: Haoming Wang
    url: "https://frank-haoming.github.io/"

toc:
  - name: Overview
  - name: Retrieve the API Key
    subsections:
      - name: "Step 1: Open the profile menu"
      - name: "Step 2: Generate a new API key"
      - name: "Step 3: Copy and store the API key"
  - name: Retrieve the Base URL and model name
    subsections:
      - name: "Step 4: Open Open Platform"
      - name: "Step 5: Record the Base URL and model name"
  - name: Outcome
  - name: Next

_styles: >
  .tutorial-info {
    background: linear-gradient(135deg, #8d2aa3 0%, #660874 100%);
    color: white;
    padding: 1.4rem 1.5rem;
    border-radius: 14px;
    margin: 1.5rem 0;
  }
  .tutorial-info a {
    color: white;
    border-bottom-color: rgba(255, 255, 255, 0.55);
  }
  .step-card {
    background: #f7f9fc;
    border-left: 4px solid #8d2aa3;
    padding: 1rem 1.3rem;
    margin: 1rem 0 1.4rem;
    border-radius: 0 10px 10px 0;
  }
  .result-list code {
    white-space: nowrap;
  }
---

## Overview

This series documents the full process of connecting OpenClaw to the ECNU AI platform. The first post focuses on the three parameters required by every later step: the `API Key`, the `Base URL`, and the model name. Once these are recorded correctly, both the local installation and the Feishu integration become much smoother.

<div class="tutorial-info">
  <strong>OpenClaw × ECNU AI Setup Series</strong><br/>
  ① <strong>Retrieve ECNU AI API credentials (this post)</strong><br/>
  ② Install OpenClaw and connect it to the model<br/>
  ③ Connect a Feishu bot<br/><br/>
  <a href="/blog/2026/openclaw-series/">View the series overview</a>
</div>

On ChatECNU, the required information is mainly split across two sections: `My Token` and `Open Platform`. This post follows the actual order of the setup process.

<div class="step-card">
  <strong>Before you begin:</strong><br/>
  • Prepare your ECNU single sign-on account<br/>
  • Sign in to <code>chat.ecnu.edu.cn</code> in a browser<br/>
  • Reserve 3 to 5 minutes to record the required values
</div>

---

## Retrieve the API Key

### Step 1: Open the profile menu

After signing in to [chat.ecnu.edu.cn](https://chat.ecnu.edu.cn), click the avatar in the lower-left corner and locate **My Token** in the profile menu.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="eager"
           path="assets/img/posts/openclaw-tutorial/api-step1-profile.png"
           title="Open My Token"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 1. Open the profile menu in the lower-left corner and locate the My Token entry."
        %}
    </div>
</div>

### Step 2: Generate a new API key

On the token page, click **+ Add new Key** to generate a new API key.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/api-step2-token.png"
           title="Generate an API key"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 2. Create a new API key on the token management page."
        %}
    </div>
</div>

### Step 3: Copy and store the API key

As soon as the key is generated, copy it and store it in a safe place. This is the value you will later paste into OpenClaw, usually beginning with `sk-`.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/api-step3-key.png"
           title="Copy the API key"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 3. Copy the generated API key and store it securely."
        %}
    </div>
</div>

<div class="step-card">
  <strong>Note:</strong> The full API key is usually shown only once when it is created. It is best to save it immediately in a password manager or another secure local location. If it is lost later, simply generate a new key.
</div>

---

## Retrieve the Base URL and model name

### Step 4: Open Open Platform

Return to the main interface and open **Open Platform** from the left-side menu.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/api-step4-platform.png"
           title="Open Open Platform"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 4. Open Open Platform from the left navigation menu."
        %}
    </div>
</div>

### Step 5: Record the Base URL and model name

On the Open Platform page, copy the **Base URL** and note the model name you plan to use. In the screenshot, example models include `ecnu-reasoner` and `ecnu-max`; when you configure OpenClaw later, use whichever model names are currently shown in your own account.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/api-step5-baseurl.png"
           title="Copy the Base URL and model name"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 5. Record the Base URL and confirm the available model names on the Open Platform page."
        %}
    </div>
</div>

These are the three values worth recording first:

| Parameter | Purpose | Example |
|------|------|------|
| `API Key` | Authentication credential | `sk-...` |
| `Base URL` | Endpoint used by OpenClaw | `https://chat.ecnu.edu.cn/open/api/v1` |
| `Model Name` | Model identifier passed to the API | `ecnu-reasoner`, `ecnu-max`, etc. |

---

## Outcome

By the end of this post, you should have prepared the core values required for the OpenClaw setup:

<div class="tutorial-info result-list">
  <strong>Completed:</strong><br/>
  1. Retrieved and stored the <code>API Key</code><br/>
  2. Recorded the <code>Base URL</code><br/>
  3. Confirmed the available model name
</div>

This step does not involve local installation yet, but it determines whether the later configuration can go through cleanly.

---

## Next

The next post moves on to the actual installation: setting up OpenClaw locally and filling in the parameters collected here during initialization.

**[OpenClaw Setup (II): Install OpenClaw and Connect ECNU AI](/blog/2026/openclaw-tutorial-2/)**
