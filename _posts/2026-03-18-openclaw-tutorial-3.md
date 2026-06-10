---
layout: distill
title: "OpenClaw Setup (III): Connect a Feishu Bot"
title_zh: "OpenClaw 配置（三）：连接飞书机器人"
date: 2026-03-17
description: Extend OpenClaw into Feishu by enabling the plugin, creating an app, importing permissions, and configuring event subscriptions.
description_zh: 通过启用插件、创建应用、导入权限并配置事件订阅，将 OpenClaw 扩展到飞书。
tags: [OpenClaw, ECNU AI, Feishu]
categories: tutorial
thumbnail: assets/img/posts/openclaw-tutorial/feishu-step13.png
giscus_comments: true
featured: false

authors:
  - name: Haoming Wang
    url: "https://frank-haoming.github.io/"

toc:
  - name: Overview
  - name: Enable the Feishu plugin
    subsections:
      - name: "Step 1: Enable the plugin and confirm its status"
  - name: Create the Feishu app and record credentials
    subsections:
      - name: "Step 2-4: Create an internal app and record its credentials"
  - name: Return to the terminal and finish the local connection
    subsections:
      - name: "Step 5-8: Start channel setup and complete the local connection"
  - name: Add capabilities and permissions in Feishu
    subsections:
      - name: "Step 9-11: Enable the bot capability and import the permissions JSON"
  - name: Configure events and publish the app
    subsections:
      - name: "Step 12-13: Enable event subscriptions and publish the app"
  - name: Outcome

_styles: >
  .tutorial-info {
    background: linear-gradient(135deg, #660874 0%, #3c0648 100%);
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
    background: #f5f9ff;
    border-left: 4px solid #8d2aa3;
    padding: 1rem 1.3rem;
    margin: 1rem 0 1.4rem;
    border-radius: 0 10px 10px 0;
  }
---

## Overview

Once the local installation is working, the most direct way to extend the same OpenClaw setup into mobile and group-chat scenarios is to connect it to a Feishu bot. This post walks through the full path: enabling the local plugin, creating the app on the Feishu Open Platform, importing permissions, subscribing to events, and publishing the app.

<div class="tutorial-info">
  <strong>OpenClaw × ECNU AI Setup Series</strong><br/>
  ① Retrieve ECNU AI API credentials<br/>
  ② Install OpenClaw and connect it to the model<br/>
  ③ <strong>Connect a Feishu bot (this post)</strong><br/><br/>
  <a href="/blog/2026/openclaw-series/">View the series overview</a>
</div>

The goal here is not to explore advanced Feishu features. The goal is to complete the most basic, reproducible integration path and get the bot running reliably.

---

## Enable the Feishu plugin

### Step 1: Enable the plugin and confirm its status

First, enable the Feishu plugin in the terminal:

```bash
openclaw plugins enable feishu
```

Then verify the plugin status:

```bash
openclaw plugins list
```

If the `feishu` entry shows `loaded`, the plugin is ready to use.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="eager"
           path="assets/img/posts/openclaw-tutorial/feishu-step1.png"
           title="Enable the Feishu plugin"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 1. Enable the Feishu plugin and confirm in plugins list that its status is loaded."
        %}
    </div>
</div>

---

## Create the Feishu app and record credentials

### Step 2-4: Create an internal app and record its credentials

Open [open.feishu.cn](https://open.feishu.cn), go to the Feishu Open Platform, and click **Create Internal App** from the internal-app page.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step2.png"
           title="Open the app creation entry"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 2. Open the internal-app page and click Create Internal App."
        %}
    </div>
</div>

Next, fill in the application name and description, then create the app.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step3.png"
           title="Fill in app information"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 3. Enter the app name and description, then create the app."
        %}
    </div>
</div>

After the app is created, open **Credentials & Basic Information** and record both the `App ID` and the `App Secret`. You will need these values immediately in the terminal.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step4.png"
           title="Record the credentials"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 4. Record the App ID and App Secret from the credentials page."
        %}
    </div>
</div>

---

## Return to the terminal and finish the local connection

### Step 5-8: Start channel setup and complete the local connection

Go back to the terminal and start the Feishu channel setup:

```bash
openclaw channels add
```

At the prompt `Configure chat channels now?`, choose `Yes`.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step5.png"
           title="Start channel setup"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 5. Run openclaw channels add and choose Yes when asked whether to configure chat channels now."
        %}
    </div>
</div>

Then enter the `App Secret` and `App ID` you recorded earlier, and continue through the connection settings. Here, `Figure 6`, `Figure 7`, and `Figure 8` each contain multiple annotated steps within a single screen, so follow the numbered order shown in the screenshots.

1. Choose **Enter App Secret** as the credential input method
2. Paste the `App Secret` and then the `App ID`
3. Set the connection mode to `WebSocket`, choose the mainland-China domain option, and select the group-chat policy
4. Keep the remaining options at their recommended defaults until `Channels updated.` appears

Recommended values for the connection settings:

| Option | Recommended value | Note |
|------|--------|------|
| Connection mode | `WebSocket` | Matches the setup in this post |
| Domain | `feishu/feishu-China` | Intended for mainland China |
| Group chat policy | `open` | Allows the bot to respond when used in group chats |

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step6.png"
           title="Enter the app credentials"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 6. Choose Enter App Secret, then continue within the same screen to paste the App Secret and App ID."
        %}
    </div>
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step7.png"
           title="Configure connection settings"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 7. On the same screen, set the connection mode to WebSocket, choose the mainland-China domain, and select the group-chat policy."
        %}
    </div>
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step8.png"
           title="Complete the local configuration"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 8. Continue through the DM access, display-name, and agent-binding prompts until Channels updated. appears."
        %}
    </div>
</div>

---

## Add capabilities and permissions in Feishu

### Step 9-11: Enable the bot capability and import the permissions JSON

Back on the Feishu Open Platform, first enable the bot capability for the app, then import the required permissions.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step9.png"
           title="Enable the bot capability"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 9. Open Add App Capability and enable the bot capability for the app."
        %}
    </div>
</div>

Next, open **Permission Management** and select **Batch Import/Export Permissions**.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step10.png"
           title="Open the permission import interface"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 10. Open Permission Management and choose Batch Import/Export Permissions."
        %}
    </div>
</div>

Paste the following JSON into the import dialog, or download the file directly and import it there:
[openclaw-feishu-permissions.json](/assets/json/openclaw-feishu-permissions.json)

<div class="step-card">
  <strong>Permissions JSON</strong> — This is the permission set required to run the Feishu bot configuration in this tutorial.
</div>

{% highlight json %}
{
  "scopes": {
    "tenant": [
      "aily:file:read",
      "aily:file:write",
      "application:application.app_message_stats.overview:readonly",
      "application:application:self_manage",
      "application:bot.menu:write",
      "cardkit:card:read",
      "cardkit:card:write",
      "contact:user.employee_id:readonly",
      "corehr:file:download",
      "event:ip_list",
      "im:chat.access_event.bot_p2p_chat:read",
      "im:chat.members:bot_access",
      "im:message",
      "im:message.group_at_msg:readonly",
      "im:message.p2p_msg:readonly",
      "im:message:readonly",
      "im:message:send_as_bot",
      "im:resource"
    ],
    "user": [
      "aily:file:read",
      "aily:file:write",
      "im:chat.access_event.bot_p2p_chat:read"
    ]
  }
}
{% endhighlight %}

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step11.png"
           title="Import the permissions JSON"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 11. Paste the JSON into the import window and continue to confirm the newly requested permissions."
        %}
    </div>
</div>

---

## Configure events and publish the app

### Step 12-13: Enable event subscriptions and publish the app

After the permission import is complete, open **Events and Callbacks**, choose **Receive events via long connection (WebSocket)**, save the setting, and add the following four event subscriptions:

- `im.message.receive_v1`
- `im.message.message_read_v1`
- `im.chat.member.bot.added_v1`
- `im.chat.member.bot.deleted_v1`

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step12.png"
           title="Configure event subscriptions"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 12. Enable WebSocket event delivery on the Events and Callbacks page and add the four required events."
        %}
    </div>
</div>

Finally, open **Version Management & Release**, fill in the version number, default capability, and release notes, and publish the app.

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid
           loading="lazy"
           path="assets/img/posts/openclaw-tutorial/feishu-step13.png"
           title="Publish the app"
           class="img-fluid rounded z-depth-1"
           zoomable=true
           caption="Figure 13. Complete the version number and release notes on the publishing page, then publish the app."
        %}
    </div>
</div>

---

## Outcome

At this stage, OpenClaw is no longer limited to the local terminal. The same model setup has been extended into the Feishu environment.

<div class="tutorial-info">
  <strong>Completed:</strong><br/>
  1. Enabled the Feishu plugin locally and created the channel<br/>
  2. Created the Feishu app and imported its required permissions<br/>
  3. Published the app and enabled WebSocket event subscriptions
</div>

You can now add the bot to a Feishu group or use it in the supported scenarios directly. The same ECNU AI endpoint can now serve both the terminal workflow and the Feishu bot workflow.
