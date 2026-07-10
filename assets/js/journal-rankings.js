document.addEventListener("DOMContentLoaded", function () {
  "use strict";

  var table = document.getElementById("journal-table");
  if (!table) return;

  var tableBody = document.getElementById("journal-tbody");
  var searchInput = document.getElementById("journal-search");
  var quartileFilter = document.getElementById("quartile-filter");
  var publisherFilter = document.getElementById("publisher-filter");
  var tagFilter = document.getElementById("tag-filter");
  var emptyState = document.getElementById("jr-empty-state");
  var resultsCount = document.getElementById("jr-results-count");
  var pagination = document.getElementById("jr-pagination");
  var source = table.dataset.source;

  var entries = [];
  var matched = [];
  var hmScores = [];
  var perPage = 25;
  var currentPage = 1;
  var requestedPage = 1;
  var currentSort = { key: "purple", dir: "desc" };
  var searchTimer;

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
    });
  }

  function numeric(value, fallback) {
    var number = parseFloat(String(value == null ? "" : value).replace(/[^0-9.-]/g, ""));
    return Number.isFinite(number) ? number : fallback;
  }

  function shortDays(value) {
    var number = numeric(value, null);
    return number == null ? "–" : number + "d";
  }

  function metric(value) {
    return value === "" || value == null || Number(value) === 0 ? "–" : escapeHtml(value);
  }

  function hmColor(value) {
    var score = numeric(value, 0);
    var index = 0;
    for (var i = 0; i < hmScores.length; i++) {
      if (hmScores[i] <= score) index = i;
    }
    var percentile = hmScores.length > 1 ? index / (hmScores.length - 1) : 1;
    if (percentile >= 0.95) return "#1a8c35";
    if (percentile >= 0.85) return "#28a745";
    if (percentile >= 0.7) return "#20a779";
    if (percentile >= 0.55) return "#167f94";
    if (percentile >= 0.4) return "#2468b4";
    if (percentile >= 0.25) return "#6610f2";
    if (percentile >= 0.1) return "#b63778";
    return "#b75b16";
  }

  function label(en, zh) {
    return '<div class="jr-mobile-label"><span class="only-en">' + en + '</span><span class="only-zh">' + zh + "</span></div>";
  }

  function detailsHtml(entry) {
    var details = [];
    if (entry.reviewTime) details.push("<div><strong>Review:</strong> " + escapeHtml(shortDays(entry.reviewTime)) + "</div>");
    if (entry.acceptanceTime) details.push("<div><strong>To Accept:</strong> " + escapeHtml(shortDays(entry.acceptanceTime)) + "</div>");
    if (entry.publicationTime) details.push("<div><strong>To Publish:</strong> " + escapeHtml(shortDays(entry.publicationTime)) + "</div>");
    if (entry.documentsCurrentYear) details.push("<div><strong>Articles:</strong> " + escapeHtml(entry.documentsCurrentYear) + "</div>");
    if (entry.documentsLastYear) details.push("<div><strong>Last Year:</strong> " + escapeHtml(entry.documentsLastYear) + "</div>");
    if (!details.length) return '<span class="text-muted">–</span>';
    return '<details class="jr-details"><summary>Details</summary><div class="jr-details-box">' + details.join("") + "</div></details>";
  }

  function renderRow(entry) {
    var external = entry.url
      ? '<a href="' + escapeHtml(entry.url) + '" target="_blank" rel="noopener noreferrer" class="jr-external-link" title="Publisher page">↗</a>'
      : "";
    var orangeScore = entry.sourceId
      ? '<a href="https://www.scopus.com/sourceid/' +
        encodeURIComponent(entry.sourceId) +
        '" target="_blank" rel="noopener noreferrer">' +
        metric(entry.orangeScore) +
        "</a>"
      : metric(entry.orangeScore);
    var tags = (entry.tags || [])
      .map(function (tag) {
        return '<span class="badge badge-light border tag-badge">' + escapeHtml(tag) + "</span>";
      })
      .join("");
    var journalQuery = encodeURIComponent(entry.journal || "");

    return (
      "<tr>" +
      '<td data-label="Journal">' +
      label("Journal", "期刊") +
      '<div class="jr-journal-name"><strong>' +
      escapeHtml(entry.journal) +
      "</strong> " +
      external +
      '<a href="/cfp/?q=' +
      journalQuery +
      '" class="jr-cfp-link" title="Search CFPs for this journal">CFP</a></div>' +
      (entry.publisher ? '<div class="small text-muted">' + escapeHtml(entry.publisher) + "</div>" : "") +
      "</td>" +
      '<td data-label="HM">' +
      label("HM", "HM 指数") +
      '<span class="hm-score" style="background-color:' +
      hmColor(entry.hm) +
      '">' +
      metric(entry.hm) +
      "</span></td>" +
      '<td data-label="Purple">' +
      label("Impact Factor", "影响因子") +
      (entry.purpleQuartile ? '<span class="badge badge-purple">' + escapeHtml(entry.purpleQuartile) + "</span><br>" : "") +
      "<small>" +
      metric(entry.purpleScore) +
      "</small></td>" +
      '<td data-label="Orange">' +
      label("CiteScore", "CiteScore") +
      (entry.orangeQuartile ? '<span class="badge badge-orange">' + escapeHtml(entry.orangeQuartile) + "</span><br>" : "") +
      "<small>" +
      orangeScore +
      "</small></td>" +
      '<td data-label="Red">' +
      label("CAS", "中科院分区") +
      (entry.redDivision ? '<span class="badge badge-red">' + escapeHtml(entry.redDivision) + "</span>" : "–") +
      "</td>" +
      '<td data-label="Decision">' +
      label("First Decision", "首次决定") +
      escapeHtml(shortDays(entry.firstDecision)) +
      "</td>" +
      '<td data-label="Accept">' +
      label("Accept Rate", "录用率") +
      metric(entry.acceptanceRate) +
      "</td>" +
      '<td data-label="More">' +
      label("More", "更多") +
      detailsHtml(entry) +
      "</td>" +
      '<td class="tags-cell" data-label="Tags">' +
      label("Tags", "标签") +
      tags +
      "</td></tr>"
    );
  }

  function updateUrl() {
    var url = new URL(window.location.href);
    var values = {
      q: searchInput.value.trim(),
      quartile: quartileFilter.value,
      publisher: publisherFilter.value,
      tag: tagFilter.value,
      sort: currentSort.key === "purple" ? "" : currentSort.key,
      dir: currentSort.dir === "desc" ? "" : currentSort.dir,
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

    function makeButton(text, page, disabled, active) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "jr-page-btn" + (active ? " active" : "");
      button.textContent = text;
      button.disabled = disabled;
      if (!disabled) {
        button.addEventListener("click", function () {
          currentPage = page;
          renderPage(true);
        });
      }
      return button;
    }

    pagination.appendChild(makeButton("‹", currentPage - 1, currentPage === 1, false));
    var total = Math.min(totalPages, 7);
    var start = Math.max(1, Math.min(currentPage - 3, totalPages - total + 1));
    for (var page = start; page < start + total; page++) {
      pagination.appendChild(makeButton(String(page), page, false, page === currentPage));
    }
    pagination.appendChild(makeButton("›", currentPage + 1, currentPage === totalPages, false));
  }

  function renderPage(shouldScroll) {
    var totalPages = Math.max(1, Math.ceil(matched.length / perPage));
    currentPage = Math.min(Math.max(1, currentPage), totalPages);
    var start = (currentPage - 1) * perPage;
    var visible = matched.slice(start, start + perPage);

    tableBody.innerHTML = visible.map(renderRow).join("");
    table.style.display = matched.length ? "" : "none";
    emptyState.style.display = matched.length ? "none" : "block";
    resultsCount.textContent = matched.length ? start + 1 + "–" + (start + visible.length) + " / " + matched.length : "0 / " + entries.length;
    document.getElementById("total-journals").textContent = matched.length;
    document.getElementById("q1-count").textContent = matched.filter(function (entry) {
      return String(entry.purpleQuartile || "").includes("Q1");
    }).length;
    renderPagination(totalPages);
    updateUrl();
    if (shouldScroll) document.querySelector(".search-filter-section").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function sortValue(entry, key) {
    if (key === "name") return String(entry.journal || "").toLowerCase();
    if (key === "decision") return numeric(entry.firstDecision, 9999);
    if (key === "accept") return numeric(entry.acceptanceRate, -1);
    if (key === "hm") return numeric(entry.hm, 0);
    if (key === "orange") return numeric(entry.orangeScore, 0);
    return numeric(entry.purpleScore, 0);
  }

  function applyFilters(resetPage) {
    var searchTerm = searchInput.value.trim().toLowerCase();
    var quartile = quartileFilter.value;
    var publisher = publisherFilter.value.toLowerCase();
    var tag = tagFilter.value.toLowerCase();

    matched = entries.filter(function (entry) {
      var tags = entry.tags || [];
      var searchBlob = [entry.journal, entry.publisher, tags.join(" ")].join(" ").toLowerCase();
      return (
        (!searchTerm || searchBlob.includes(searchTerm)) &&
        (!quartile || String(entry.purpleQuartile || "").includes(quartile)) &&
        (!publisher || String(entry.publisher || "").toLowerCase() === publisher) &&
        (!tag ||
          tags.some(function (item) {
            return String(item).toLowerCase() === tag;
          }))
      );
    });

    matched.sort(function (a, b) {
      var aValue = sortValue(a, currentSort.key);
      var bValue = sortValue(b, currentSort.key);
      var result = typeof aValue === "string" ? aValue.localeCompare(bValue) : aValue - bValue;
      if (currentSort.key === "decision") {
        if (aValue === 9999 && bValue !== 9999) return 1;
        if (bValue === 9999 && aValue !== 9999) return -1;
      }
      return currentSort.dir === "asc" ? result : -result;
    });

    if (resetPage !== false) currentPage = 1;
    renderPage(false);
  }

  function restoreUrlState() {
    var params = new URLSearchParams(window.location.search);
    searchInput.value = params.get("q") || "";
    quartileFilter.value = params.get("quartile") || "";
    publisherFilter.value = params.get("publisher") || "";
    tagFilter.value = params.get("tag") || "";
    currentSort.key = ["name", "hm", "purple", "orange", "decision", "accept"].includes(params.get("sort")) ? params.get("sort") : "purple";
    currentSort.dir = params.get("dir") === "asc" ? "asc" : "desc";
    requestedPage = Math.max(1, parseInt(params.get("page"), 10) || 1);
    currentPage = requestedPage;
  }

  document.querySelectorAll(".sortable").forEach(function (header) {
    header.addEventListener("click", function () {
      var key = this.dataset.sort;
      currentSort.dir = currentSort.key === key && currentSort.dir === "desc" ? "asc" : "desc";
      currentSort.key = key;
      document.querySelectorAll(".sortable").forEach(function (item) {
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
  quartileFilter.addEventListener("change", function () {
    applyFilters(true);
  });
  publisherFilter.addEventListener("change", function () {
    applyFilters(true);
  });
  tagFilter.addEventListener("change", function () {
    applyFilters(true);
  });

  restoreUrlState();
  fetch(source, { credentials: "same-origin" })
    .then(function (response) {
      if (!response.ok) throw new Error("Unable to load journal data");
      return response.json();
    })
    .then(function (data) {
      entries = data;
      hmScores = entries
        .map(function (entry) {
          return numeric(entry.hm, null);
        })
        .filter(function (score) {
          return score != null;
        })
        .sort(function (a, b) {
          return a - b;
        });
      currentPage = requestedPage;
      applyFilters(false);
      window.dispatchEvent(new Event("context-rail:ready"));
    })
    .catch(function () {
      table.style.display = "none";
      emptyState.style.display = "block";
      emptyState.innerHTML =
        '<p><span class="only-en">The journal data could not be loaded. Please refresh the page.</span><span class="only-zh">期刊数据加载失败，请刷新页面。</span></p>';
      resultsCount.textContent = "";
    });
});
