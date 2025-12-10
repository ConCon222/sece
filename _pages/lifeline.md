---
layout: page
title: Life Line
permalink: /lifeline/
description: 
nav: true
nav_order: 5  # 导航栏顺序，数字越小越靠前
---

<!-- ==================== 隐藏默认标题 ==================== -->
<style>
  .post-title { display: none; }
  .post-description { display: none; }
</style>

<!-- ==================== 主要样式 ==================== -->
<style>

/* ---------- 时间线容器 ---------- */
.lifeline {
  position: relative;
  max-width: 900px;        /* 最大宽度，可调大/小 */
  margin: 0 auto;
  padding: 2rem 0;
}

/* ---------- 中间的竖线 ---------- */
.lifeline::before {
  content: '';
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;              /* 竖线粗细 */
  height: 100%;
  background: #cbd5e1;     /* 竖线颜色 */
}

/* ---------- 顶部标题区域 ---------- */
.lifeline-header {
  text-align: center;
  margin-bottom: 2rem;
}

.lifeline-hint {
  color: #94a3b8;          /* 提示文字颜色 */
  font-size: 0.875rem;     /* 提示文字大小 */
  margin-bottom: 1rem;
}

/* ---------- 展开/折叠按钮 ---------- */
.lifeline-controls {
  display: flex;
  justify-content: center;
  gap: 0.75rem;            /* 按钮间距 */
}

.lifeline-btn {
  padding: 0.375rem 1rem;
  font-size: 0.75rem;
  background: #f1f5f9;     /* 按钮背景色 */
  color: #475569;          /* 按钮文字色 */
  border: none;
  border-radius: 9999px;   /* 圆角按钮 */
  cursor: pointer;
  transition: all 0.2s;
}

.lifeline-btn:hover {
  background: #e2e8f0;     /* 悬停背景色 */
}

/* ---------- 年份区块 ---------- */
.year-section {
  position: relative;
  margin-bottom: 1rem;
}

/* ---------- 年份标签（可点击） ---------- */
.year-marker {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  z-index: 10;
  margin: 1.5rem 0;
  cursor: pointer;
}

.year-label {
  background: #334155;     /* 年份标签背景色 */
  color: white;
  font-size: 1.25rem;      /* 年份字体大小 */
  font-weight: 700;
  padding: 0.625rem 1.5rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.year-label:hover {
  background: #475569;     /* 悬停背景色 */
  transform: scale(1.05);  /* 悬停放大效果 */
}

.year-count {
  background: #475569;     /* 事件数量标签背景 */
  color: white;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.year-chevron {
  font-size: 0.875rem;
  color: #94a3b8;          /* 箭头颜色 */
}

/* ---------- 事件容器（折叠动画） ---------- */
.events-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;               /* 事件卡片间距 */
  overflow: hidden;
  max-height: 2000px;      /* 展开时最大高度，事件多可调大 */
  transition: max-height 0.3s ease;
}

.events-container.collapsed {
  max-height: 0;           /* 折叠时高度为0 */
}

/* ---------- 事件卡片 ---------- */
.event-card {
  position: relative;
  width: 45%;              /* 卡片宽度，相对于容器 */
  background: #f8fafc;     /* 卡片背景色 */
  border: 1px solid #e2e8f0;
  border-radius: 1rem;     /* 卡片圆角 */
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.3s ease;
}

.event-card:hover {
  transform: translateY(-2px);  /* 悬停上移效果 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 左侧卡片 */
.event-card.left {
  margin-left: auto;
  margin-right: 55%;
  text-align: right;
}

/* 右侧卡片 */
.event-card.right {
  margin-left: 55%;
  margin-right: auto;
  text-align: left;
}

/* ---------- 卡片上的圆点（连接线上的点） ---------- */
.event-card::before {
  content: '';
  position: absolute;
  top: 50%;
  width: 12px;             /* 圆点大小 */
  height: 12px;
  background: white;
  border: 3px solid #94a3b8;  /* 圆点边框 */
  border-radius: 50%;
  transform: translateY(-50%);
}

.event-card.left::before {
  right: -8%;              /* 左侧卡片的点在右边 */
}

.event-card.right::before {
  left: -8%;               /* 右侧卡片的点在左边 */
}

/* ---------- 卡片头部（标签+图标） ---------- */
.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.event-card.left .event-header {
  flex-direction: row;
}

.event-card.right .event-header {
  flex-direction: row-reverse;
}

/* ---------- 事件类型标签 ---------- */
.event-tag {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  color: white;
}

/* 各类型标签颜色 - 可自定义 */
.tag-award { background: #f59e0b; }       /* 橙色 - 奖项 */
.tag-honor { background: #a855f7; }       /* 紫色 - 荣誉 */
.tag-publication { background: #3b82f6; } /* 蓝色 - 发表 */
.tag-milestone { background: #10b981; }   /* 绿色 - 里程碑 */
.tag-personal { background: #ec4899; }    /* 粉色 - 个人 */
.tag-work { background: #6366f1; }        /* 靛蓝 - 工作 */
.tag-project { background: #06b6d4; }     /* 青色 - 项目 */
.tag-talk { background: #ef4444; }  /* 红色 - 醒目，代表演讲/发声 */
.tag-service { background: #8b5cf6; }     /* 蓝紫色 - 代表服务/管理 */
.tag-exchange    { background: #ec4899; } /* 粉色 - 活跃、社交 */

.event-icon {
  font-size: 1.5rem;       /* 图标大小 */
}

/* ---------- 事件标题 ---------- */
.event-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
}

/* ---------- 事件详情（点击展开） ---------- */
.event-details {
  display: none;           /* 默认隐藏 */
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.event-card.expanded .event-details {
  display: block;          /* 展开时显示 */
}

.event-date {
  font-size: 0.75rem;
  font-weight: 500;
  color: #94a3b8;
}

.event-description {
  font-size: 0.85rem;
  color: #64748b;
  margin-top: 0.25rem;
}

/* ---------- 底部结束点 ---------- */
.lifeline-end {
  display: flex;
  justify-content: center;
  padding: 1.5rem 0;
  position: relative;
  z-index: 10;
}

.lifeline-end-dot {
  width: 1.5rem;
  height: 1.5rem;
  background: #cbd5e1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lifeline-end-dot::before {
  content: '';
  width: 0.5rem;
  height: 0.5rem;
  background: #64748b;
  border-radius: 50%;
}

/* ---------- 移动端适配 ---------- */
@media (max-width: 768px) {
  /* 竖线移到左侧 */
  .lifeline::before {
    left: 20px;
  }

  /* 所有卡片靠右排列 */
  .event-card {
    width: calc(100% - 50px);
    margin-left: 50px !important;
    margin-right: 0 !important;
    text-align: left !important;
  }

  .event-card .event-header {
    flex-direction: row-reverse !important;
  }

  .event-card::before {
    left: -40px !important;
    right: auto !important;
  }
}
</style>

<!-- ==================== 数据处理 ==================== -->
{% assign events_by_year = site.data.lifeline.events | group_by: "year" | sort: "name" | reverse %}
{% assign total_years = events_by_year | size %}
<!-- 
  数据来源: _data/lifeline.yml
  group_by: "year" - 按年份分组
  sort: "name" - 按年份排序
  reverse - 倒序（最新的在前）
-->

<!-- ==================== 页面结构 ==================== -->
<div class="lifeline-header">
  <h2>Life Line: {{ site.data.lifeline.events | size }} Moments · {{ total_years }} Years</h2>
  <p class="lifeline-hint">(点击节点查看详情 · Click nodes to expand)</p>
  <div class="lifeline-controls">
    <button class="lifeline-btn" onclick="expandAllYears()">Expand All</button>
    <button class="lifeline-btn" onclick="collapseAllYears()">Collapse All</button>
  </div>
</div>

<div class="lifeline">
  <!-- 遍历每一年 -->
  {% for year in events_by_year %}
  <div class="year-section">
    <!-- 年份标签 -->
    <div class="year-marker" onclick="toggleYear('{{ year.name }}')">
      <span class="year-label">
        {{ year.name }}
        <span class="year-count">{{ year.items | size }}</span>
        <span class="year-chevron" id="chevron-{{ year.name }}">▼</span>
      </span>
    </div>
    
    <!-- 该年的所有事件 -->
    <div class="events-container" id="events-{{ year.name }}">
      {% for event in year.items %}
      <!-- 奇偶判断：奇数在左，偶数在右 -->
      {% assign position = forloop.index | modulo: 2 %}
      <div class="event-card {% if position == 1 %}left{% else %}right{% endif %}" onclick="toggleCard(this)">
        <div class="event-header">
          <!-- 类型标签，对应 _data/lifeline.yml 中的 tags -->
          <span class="event-tag tag-{{ event.type }}">{{ site.data.lifeline.tags[event.type] }}</span>
          <!-- 图标，用 emoji -->
          <span class="event-icon">{{ event.icon }}</span>
        </div>
        <div class="event-title">{{ event.title }}</div>
        <!-- 点击卡片后展开的详情 -->
        <div class="event-details">
          <span class="event-date">{{ event.date }}</span>
          {% if event.description and event.description != "" %}
          <p class="event-description">{{ event.description }}</p>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endfor %}

  <!-- 时间线底部的结束点 -->
  <div class="lifeline-end">
    <div class="lifeline-end-dot"></div>
  </div>
</div>

<!-- ==================== 交互脚本 ==================== -->
<script>
// 切换某一年的展开/折叠
function toggleYear(year) {
  const container = document.getElementById('events-' + year);
  const chevron = document.getElementById('chevron-' + year);
  container.classList.toggle('collapsed');
  chevron.textContent = container.classList.contains('collapsed') ? '▶' : '▼';
}

// 切换单个卡片的展开/折叠
function toggleCard(card) {
  card.classList.toggle('expanded');
}

// 展开所有年份
function expandAllYears() {
  document.querySelectorAll('.events-container').forEach(el => el.classList.remove('collapsed'));
  document.querySelectorAll('.year-chevron').forEach(el => el.textContent = '▼');
}

// 折叠所有年份
function collapseAllYears() {
  document.querySelectorAll('.events-container').forEach(el => el.classList.add('collapsed'));
  document.querySelectorAll('.year-chevron').forEach(el => el.textContent = '▶');
}
</script>