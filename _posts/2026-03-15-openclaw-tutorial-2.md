---
layout: distill
title: "OpenClaw Setup (II): Install OpenClaw and Connect ECNU AI"
title_zh: "OpenClaw 配置（二）：安装 OpenClaw 并连接 ECNU AI"
date: 2026-03-15
description: Install OpenClaw locally, connect it to the ECNU AI platform, and verify that the environment works end to end.
description_zh: 在本地安装 OpenClaw，连接 ECNU AI 平台，并验证环境端到端可用。
tags: [OpenClaw, ECNU AI]
categories: tutorial
thumbnail: assets/img/posts/openclaw-tutorial/install-step0.png
giscus_comments: true
featured: false

authors:
  - name: Haoming Wang
    url: "https://frank-haoming.github.io/"

toc:
  - name: Overview
  - name: Run the installer
    subsections:
      - name: "Step 1: Execute the installation command"
      - name: "Step 2: Confirm the installation prompt"
      - name: "Step 3-4: Choose QuickStart and switch to Custom Provider"
  - name: Connect the ECNU AI platform
    subsections:
      - name: "Step 5-9: Complete model configuration within a single screen"
  - name: Finish initialization
    subsections:
      - name: "Step 10-15: Complete the remaining options and enter the Web UI"
  - name: Verify the result
  - name: Next

_styles: >
  .tutorial-info {
    background: linear-gradient(135deg, #b73a8e 0%, #7d1a8c 100%);
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
    background: #fcf7f8;
    border-left: 4px solid #d74b6c;
    padding: 1rem 1.3rem;
    margin: 1rem 0 1.4rem;
    border-radius: 0 10px 10px 0;
  }
---

## Overview

In the first post, we collected the `API Key`, `Base URL`, and model name. The next step is to install OpenClaw locally and map those values into the initialization flow correctly.

<div class="tutorial-info">
  <strong>OpenClaw × ECNU AI Setup Series</strong><br/>
  ① Retrieve ECNU AI API credentials<br/>
  ② <strong>Install OpenClaw and connect it to the model (this post)</strong><br/>
  ③ Connect a Feishu bot<br/><br/>
  <a href="/blog/2026/openclaw-series/">View the series overview</a>
</div>

If your goal is to reach a minimal working local environment as quickly as possible, this post covers exactly that path.

<div class="step-card">
  <strong>Goal of this post:</strong><br/>
  • Install OpenClaw locally<br/>
  • Connect it to the ECNU AI platform through a custom provider<br/>
  • Confirm that the model can respond correctly in your local environment
</div>

---

## Run the installer

### Step 1: Execute the installation command

Run the appropriate installation command for your operating system.

**macOS / Linux**

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

**Windows PowerShell**

```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```

**Windows CMD**

```cmd
curl -fsSL https://openclaw.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="eager"
           path="assets/img/posts/openclaw-tutorial/install-step1-download.png"
           title="Run the installation command"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 1. Run the installation command in the terminal and wait for the download and initialization to complete."
        %}
    </div>
</div>

### Step 2: Confirm the installation prompt

Once the script finishes downloading the required components, OpenClaw opens its onboarding screen. Read the prompt and confirm that you want to continue.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step2-welcome.png"
           title="Welcome screen"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 2. Review the onboarding prompt and confirm the installation."
        %}
    </div>
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step3-quickstart.png"
           title="Choose QuickStart"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 3. On the same screen, first choose QuickStart and then switch to Custom Provider."
        %}
    </div>
</div>

### Step 3-4: Choose QuickStart and switch to Custom Provider

No additional values need to be entered here. Simply follow the annotations in `Figure 3` to enter the custom provider flow.

---

## Connect the ECNU AI platform

### Step 5-9: Complete model configuration within a single screen

From this point on, `Figure 4` already contains steps 5 through 9 within a single interface. Follow the order shown in the screenshot:

1. Enter the `Base URL` recorded in the first post
2. Choose **Paste API key now**
3. Paste the saved `API Key`
4. Select **Unknown (detect automatically)**
5. Enter the model name you want to use, such as `ecnu-reasoner` or `ecnu-max`

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step4-provider.png"
           title="Complete model configuration within a single screen"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 4. Steps 5-9 are grouped within one interface: fill in the Base URL, API key, and model name in order."
        %}
    </div>
</div>

---

## Finish initialization

### Step 10-15: Complete the remaining options and enter the Web UI

After the model connection is in place, the rest of the onboarding flow mainly consists of optional settings. There is no need to over-optimize these choices during the first pass; follow the key selections marked in each screenshot.

- If you are unsure about chat channels, search providers, or extra skills, it is fine to skip them for now
- If OpenClaw asks for additional API keys you do not need, choose `No`
- If you want a visual interface, select `Open the Web UI` in the final step

This part maps `Figure 5` through `Figure 10` to steps 10 through 15.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step5-baseurl.png"
           title="Choose a chat channel"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 5. Step 10: choose a chat channel. If you only need a local setup for now, select Skip for now."
        %}
    </div>
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step6-apikey-option.png"
           title="Configure search capability"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 6. Step 11: the search provider can be skipped during the initial setup and added later if needed."
        %}
    </div>
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step7-apikey-paste.png"
           title="Choose skills"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 7. Step 12: select skills if you want them, or skip them to keep the setup minimal."
        %}
    </div>
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step8-detect-model.png"
           title="Handle extra key prompts"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 8. Step 13: if extra skill-specific API key prompts appear and you do not need them, choose No."
        %}
    </div>
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step9-model-name.png"
           title="Configure hooks"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 9. Step 14: enable hooks only if they match your workflow; leaving the default is fine for a first setup."
        %}
    </div>
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step10-tools.png"
           title="Enter the Web UI"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 10. Step 15: choose Open the Web UI to enter the graphical interface."
        %}
    </div>
</div>

---

## Verify the result

After finishing the setup, ask a simple question in the interface. If the model responds correctly, the local installation and API connection are working as expected.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/install-step11-search.png"
           title="Verify the Web UI"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 11. Once the Web UI opens, ask a simple question to confirm that the model connection is working."
        %}
    </div>
</div>

<div class="step-card">
  <strong>If something goes wrong:</strong> Check the three core values first: <code>Base URL</code>, <code>API Key</code>, and the model name. If those are correct but the onboarding flow became inconsistent, reinstalling is usually faster than unwinding the configuration manually.
</div>

At this point, you already have a usable local OpenClaw environment. The next step is to extend the same setup into Feishu.

---

## Next

The next post covers how to connect OpenClaw to a Feishu bot so that the same model can be used in mobile and group-chat scenarios.

**[OpenClaw Setup (III): Connect a Feishu Bot](/blog/2026/openclaw-tutorial-3/)**
