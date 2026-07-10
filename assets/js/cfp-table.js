document.addEventListener("DOMContentLoaded", function () {
  "use strict";

  var table = document.getElementById("cfp-table");
  if (!table) return;

  var tableBody = document.getElementById("cfp-table-body");
  var searchInput = document.getElementById("cfp-search");
  var tagFilter = document.getElementById("cfp-tag-filter");
  var publisherFilter = document.getElementById("cfp-publisher-filter");
  var showExpiredToggle = document.getElementById("cfp-show-expired");
  var emptyState = document.getElementById("cfp-empty-state");
  var resultsCount = document.getElementById("cfp-results-count");
  var pagination = document.getElementById("cfp-pagination");
  var source = table.dataset.source;

  var entries = [];
  var matched = [];
  var perPage = 25;
  var currentPage = 1;
  var requestedPage = 1;
  var currentSort = { key: "deadline", dir: "asc" };
  var searchTimer;

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
    });
  }

  function truncate(value, max) {
    var text = String(value || "").trim();
    return text.length > max ? text.slice(0, max - 1).trimEnd() + "…" : text;
  }

  function parseDeadline(value) {
    if (!value || value === "9999-99-99") return null;
    var parts = value.split("-").map(Number);
    return new Date(parts[0], parts[1] - 1, parts[2], 23, 59, 59);
  }

  function daysUntil(value) {
    var deadline = parseDeadline(value);
    if (!deadline) return null;
    return Math.ceil((deadline - new Date()) / 86400000);
  }

  function isExpired(entry) {
    var days = daysUntil(entry.deadlineSort);
    return days != null && days < 0;
  }

  function deadlineHtml(entry) {
    var days = daysUntil(entry.deadlineSort);
    if (entry.deadlineSort === "9999-99-99" || !entry.deadlineSort) {
      return '<span class="badge deadline-tba">TBA</span>';
    }
    if (days != null && days < 0) {
      return '<span class="badge deadline-expired">Expired</span>';
    }
    var urgent = days != null && days <= 14;
    var count = days == null ? "" : days + " day" + (days === 1 ? "" : "s") + " left";
    return (
      '<span class="badge ' +
      (urgent ? "deadline-urgent" : "deadline-active") +
      '">' +
      escapeHtml(entry.deadlineSort) +
      "</span>" +
      '<div class="countdown-text' +
      (days > 30 ? " comfortable" : "") +
      '">' +
      escapeHtml(count) +
      "</div>"
    );
  }

  function detailsHtml(entry) {
    var description = String(entry.description || "").trim();
    var editors = String(entry.editors || "").trim();
    var abstractDeadline = String(entry.abstractDeadline || "").trim();
    if ((!description || description === "N/A") && (!editors || editors === "N/A") && !abstractDeadline) return "";

    var parts = [];
    if (abstractDeadline) {
      parts.push(
        '<div class="mb-2"><span class="cfp-meta-label"><span class="only-en">Abstract deadline:</span><span class="only-zh">摘要截止：</span></span> ' +
          escapeHtml(abstractDeadline) +
          "</div>"
      );
    }
    if (editors && editors !== "N/A") {
      parts.push(
        '<div class="mb-2"><span class="cfp-meta-label"><span class="only-en">Guest editors:</span><span class="only-zh">特邀编辑：</span></span> ' +
          escapeHtml(editors) +
          "</div>"
      );
    }
    if (description && description !== "N/A") {
      parts.push(
        '<div class="mt-2"><span class="cfp-meta-label"><span class="only-en">Scope:</span><span class="only-zh">征稿范围：</span></span>' +
          '<p class="mb-0 text-muted cfp-full-scope">' +
          escapeHtml(truncate(description, 400)) +
          "</p></div>"
      );
    }
    return (
      '<details class="cfp-more"><summary><span class="only-en">More</span><span class="only-zh">更多</span></summary>' +
      '<div class="cfp-details-box">' +
      parts.join("") +
      "</div></details>"
    );
  }

  function renderRow(entry) {
    var tags = (entry.tags || [])
      .map(function (tag) {
        return '<span class="badge badge-light border tag-badge">' + escapeHtml(tag) + "</span>";
      })
      .join("");
    var description = String(entry.description || "").trim();
    var scope = description && description !== "N/A" ? '<p class="cfp-scope">' + escapeHtml(truncate(description, 150)) + "</p>" : "";
    var journalQuery = encodeURIComponent(entry.journal || "");

    return (
      '<tr class="cfp-row">' +
      '<td data-label="Deadline"><div class="cfp-mobile-label"><span class="only-en">Deadline</span><span class="only-zh">截止日期</span></div>' +
      deadlineHtml(entry) +
      '<div class="small text-muted mt-1">' +
      escapeHtml(entry.deadline || "See Website") +
      "</div></td>" +
      '<td data-label="Journal"><div class="cfp-mobile-label"><span class="only-en">Journal</span><span class="only-zh">期刊</span></div><div class="cfp-journal-cell"><b>' +
      escapeHtml(entry.journal) +
      '</b><a href="/jrank/?q=' +
      journalQuery +
      '" class="cfp-journal-link" title="View journal metrics">IF/HM</a><div class="small text-muted mt-1"><i>' +
      escapeHtml(entry.publisher) +
      "</i></div></div></td>" +
      '<td data-label="Topic & Details"><a href="' +
      escapeHtml(entry.url) +
      '" target="_blank" rel="noopener noreferrer" class="cfp-title">' +
      escapeHtml(entry.title) +
      "</a>" +
      scope +
      '<div class="cfp-row-actions"><a href="' +
      escapeHtml(entry.url) +
      '" target="_blank" rel="noopener noreferrer" class="cfp-cta"><span class="only-en">View call &amp; submit&nbsp;↗</span><span class="only-zh">查看征稿并投稿&nbsp;↗</span></a>' +
      detailsHtml(entry) +
      "</div></td>" +
      '<td data-label="Tags"><div class="cfp-mobile-label"><span class="only-en">Tags</span><span class="only-zh">标签</span></div>' +
      tags +
      "</td></tr>"
    );
  }

  function updateUrl() {
    var url = new URL(window.location.href);
    var values = {
      q: searchInput.value.trim(),
      tag: tagFilter.value,
      publisher: publisherFilter.value,
      expired: showExpiredToggle.checked ? "1" : "",
      sort: currentSort.key === "deadline" ? "" : currentSort.key,
      dir: currentSort.dir === "asc" ? "" : currentSort.dir,
      page: currentPage > 1 ? String(currentPage) : "",
    };
    Object.keys(values).forEach(function (key) {
      if (values[key]) url.searchParams.set(key, values[key]);
      else url.searchParams.delete(key);
    });
    history.replaceState(null, "", url.pathname + url.search + url.hash);
  }

  function renderPagination(totalPages) {
    pagination.innerHTML = "";
    if (totalPages <= 1) return;

    function button(label, page, disabled, active) {
      var element = document.createElement("button");
      element.type = "button";
      element.className = "cfp-page-btn" + (active ? " active" : "");
      element.textContent = label;
      element.disabled = disabled;
      if (!disabled) {
        element.addEventListener("click", function () {
          currentPage = page;
          renderPage(true);
        });
      }
      return element;
    }

    pagination.appendChild(button("‹", currentPage - 1, currentPage === 1, false));
    var total = Math.min(totalPages, 7);
    var start = Math.max(1, Math.min(currentPage - 3, totalPages - total + 1));
    for (var page = start; page < start + total; page++) {
      pagination.appendChild(button(String(page), page, false, page === currentPage));
    }
    pagination.appendChild(button("›", currentPage + 1, currentPage === totalPages, false));
  }

  function renderPage(shouldScroll) {
    var totalPages = Math.max(1, Math.ceil(matched.length / perPage));
    currentPage = Math.min(currentPage, totalPages);
    var start = (currentPage - 1) * perPage;
    var visible = matched.slice(start, start + perPage);

    tableBody.innerHTML = visible.map(renderRow).join("");
    table.style.display = matched.length ? "" : "none";
    emptyState.style.display = matched.length ? "none" : "block";
    resultsCount.textContent = matched.length
      ? "Showing " + (start + 1) + "–" + (start + visible.length) + " of " + matched.length + " entries"
      : "0 matching calls for papers";
    renderPagination(totalPages);
    updateUrl();
    if (shouldScroll) document.querySelector(".cfp-filter-section").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function applyFilters(resetPage) {
    var searchTerm = searchInput.value.trim().toLowerCase();
    var selectedTag = tagFilter.value;
    var selectedPublisher = publisherFilter.value.toLowerCase();
    var showExpired = showExpiredToggle.checked;

    matched = entries.filter(function (entry) {
      var tags = entry.tags || [];
      var searchBlob = [entry.journal, entry.title, entry.publisher, tags.join(" ")].join(" ").toLowerCase();
      return (
        (showExpired || !isExpired(entry)) &&
        (!searchTerm || searchBlob.includes(searchTerm)) &&
        (!selectedTag || tags.includes(selectedTag)) &&
        (!selectedPublisher || String(entry.publisher || "").toLowerCase() === selectedPublisher)
      );
    });

    matched.sort(function (a, b) {
      var aValue = currentSort.key === "journal" ? String(a.journal || "").toLowerCase() : a.deadlineSort || "9999-99-99";
      var bValue = currentSort.key === "journal" ? String(b.journal || "").toLowerCase() : b.deadlineSort || "9999-99-99";
      var result = aValue.localeCompare(bValue);
      return currentSort.dir === "asc" ? result : -result;
    });
    if (resetPage !== false) currentPage = 1;
    renderPage(false);
  }

  function restoreUrlState() {
    var params = new URLSearchParams(window.location.search);
    searchInput.value = params.get("q") || "";
    tagFilter.value = params.get("tag") || "";
    publisherFilter.value = params.get("publisher") || "";
    showExpiredToggle.checked = params.get("expired") === "1";
    currentSort.key = params.get("sort") === "journal" ? "journal" : "deadline";
    currentSort.dir = params.get("dir") === "desc" ? "desc" : "asc";
    requestedPage = Math.max(1, parseInt(params.get("page"), 10) || 1);
    currentPage = requestedPage;
  }

  document.querySelectorAll(".cfp-sortable").forEach(function (header) {
    header.addEventListener("click", function () {
      var key = this.dataset.sort;
      currentSort.dir = currentSort.key === key && currentSort.dir === "asc" ? "desc" : "asc";
      currentSort.key = key;
      document.querySelectorAll(".cfp-sortable").forEach(function (item) {
        item.classList.remove("sort-asc", "sort-desc");
      });
      this.classList.add(currentSort.dir === "asc" ? "sort-asc" : "sort-desc");
      applyFilters(true);
    });
  });

  searchInput.addEventListener("input", function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () {
      applyFilters(true);
    }, 180);
  });
  tagFilter.addEventListener("change", function () {
    applyFilters(true);
  });
  publisherFilter.addEventListener("change", function () {
    applyFilters(true);
  });
  showExpiredToggle.addEventListener("change", function () {
    applyFilters(true);
  });

  restoreUrlState();
  fetch(source, { credentials: "same-origin" })
    .then(function (response) {
      if (!response.ok) throw new Error("Unable to load CFP data");
      return response.json();
    })
    .then(function (data) {
      entries = data;
      currentPage = requestedPage;
      applyFilters(false);
      window.dispatchEvent(new Event("context-rail:ready"));
    })
    .catch(function () {
      table.style.display = "none";
      emptyState.style.display = "block";
      emptyState.innerHTML =
        '<p><span class="only-en">The CFP data could not be loaded. Please refresh the page.</span><span class="only-zh">征稿数据加载失败，请刷新页面。</span></p>';
      resultsCount.textContent = "";
    });
});
