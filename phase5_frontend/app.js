/**
 * Phase 5 — Chat UI: calls POST /chat, displays answer and citation links.
 * Facts-only; no investment advice.
 * Shows data last_updated from Phase 6 scheduler (when data was last fetched).
 */

function formatLastUpdated(dateStr) {
  if (!dateStr || dateStr.length < 10) return null;
  var d = new Date(dateStr + "T00:00:00Z");
  if (isNaN(d.getTime())) return null;
  var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return d.getUTCDate() + " " + months[d.getUTCMonth()] + " " + d.getUTCFullYear();
}

function getApiBase() {
  var h = typeof window !== "undefined" && window.location && window.location.hostname;
  if (h === "localhost" || h === "127.0.0.1") return "http://127.0.0.1:8000";
  if (typeof API_BASE_URL !== "undefined" && API_BASE_URL) return API_BASE_URL;
  return "";
}

function loadDataLastUpdated() {
  var el = document.getElementById("data-last-updated");
  if (!el) return;
  var base = getApiBase();
  fetch(base + "/meta")
    .then(function (res) { return res.ok ? res.json() : null; })
    .then(function (data) {
      if (data && data.last_updated) {
        var formatted = formatLastUpdated(data.last_updated);
        el.textContent = formatted ? "Data last updated: " + formatted + "." : "";
        el.style.display = formatted ? "block" : "none";
      } else {
        el.textContent = "";
        el.style.display = "none";
      }
    })
    .catch(function () {
      el.textContent = "";
      el.style.display = "none";
    });
}

/* ── Fund filter (multi-select checkboxes) ── */

var _fundKeywords = [];
var _onFundSelectionChanged = null;

var _KEYWORD_MAP = [
  { keywords: ["large and mid cap", "large & mid cap"], id: "2874" },
  { keywords: ["largemidcap 250", "large midcap 250", "largemidcap", "nifty largemidcap"], id: "1047724" },
  { keywords: ["nifty next 50", "next 50"], id: "1040010" },
  { keywords: ["large cap", "largecap"], id: "2989" },
  { keywords: ["flexi cap", "flexicap"], id: "3184" },
  { keywords: ["elss", "tax saver", "taxsaver", "elss tax"], id: "2685" },
  { keywords: ["mid cap", "midcap"], id: "3097" },
  { keywords: ["housing"], id: "9006" },
];

function detectMentionedFundIds(query) {
  var q = query.toLowerCase();
  var found = {};
  for (var i = 0; i < _KEYWORD_MAP.length; i++) {
    var entry = _KEYWORD_MAP[i];
    for (var j = 0; j < entry.keywords.length; j++) {
      if (q.indexOf(entry.keywords[j]) !== -1) {
        found[entry.id] = true;
        break;
      }
    }
  }
  return Object.keys(found);
}

function getFundNameById(id) {
  for (var i = 0; i < _fundKeywords.length; i++) {
    if (_fundKeywords[i].id === id) return _fundKeywords[i].name;
  }
  return id;
}

function getSelectedFundNames(ids) {
  if (!ids || ids.length === 0) return [];
  var names = [];
  for (var i = 0; i < ids.length; i++) {
    names.push(getFundNameById(ids[i]));
  }
  return names;
}

function renderSelectionNameChips(container, names) {
  if (!container) return;
  container.innerHTML = "";
  if (!names || names.length === 0) {
    container.textContent = "No funds selected.";
    return;
  }
  for (var i = 0; i < names.length; i++) {
    var chip = document.createElement("span");
    chip.className = "fund-name-chip fund-name-chip-" + (i % 3);
    chip.textContent = names[i];
    container.appendChild(chip);
  }
}

var _FALLBACK_FUNDS = [
  { id: "2989", name: "HDFC Large Cap Fund Direct Plan Growth" },
  { id: "3184", name: "HDFC Flexi Cap Fund Direct Plan Growth" },
  { id: "2685", name: "HDFC ELSS Tax Saver Direct Plan Growth" },
  { id: "1040010", name: "HDFC Nifty Next 50 Index Fund Direct Growth" },
  { id: "3097", name: "HDFC Mid Cap Fund Direct Plan Growth" },
  { id: "9006", name: "HDFC Housing Opportunities Fund Direct Growth" },
  { id: "1047724", name: "HDFC Nifty LargeMidcap 250 Index Fund Direct Growth" },
  { id: "2874", name: "HDFC Large and Mid Cap Fund Direct Growth" },
];

function _renderFundCheckboxes(funds, listEl) {
  _fundKeywords = funds.map(function (f) {
    return { id: f.id, name: f.name.replace(/ Direct (Plan )?Growth$/, "") };
  });
  listEl.innerHTML = "";

  var selectAllLabel = document.createElement("label");
  selectAllLabel.className = "fund-checkbox fund-checkbox-select-all";
  var selectAllCb = document.createElement("input");
  selectAllCb.type = "checkbox";
  selectAllCb.className = "fund-cb fund-cb-select-all";
  selectAllCb.value = "";
  selectAllCb.checked = false;
  selectAllCb.setAttribute("aria-label", "Select all funds");
  var selectAllSpan = document.createElement("span");
  selectAllSpan.textContent = "Select all funds";
  selectAllLabel.appendChild(selectAllCb);
  selectAllLabel.appendChild(selectAllSpan);
  listEl.appendChild(selectAllLabel);

  selectAllCb.addEventListener("change", function () {
    var cbs = listEl.querySelectorAll(".fund-cb-fund");
    for (var i = 0; i < cbs.length; i++) {
      cbs[i].checked = selectAllCb.checked;
    }
    dismissFundWarnings();
    if (_onFundSelectionChanged) _onFundSelectionChanged();
  });

  funds.forEach(function (fund) {
    var label = document.createElement("label");
    label.className = "fund-checkbox";
    var cb = document.createElement("input");
    cb.type = "checkbox";
    cb.className = "fund-cb fund-cb-fund";
    cb.value = fund.id;
    cb.checked = false;
    var span = document.createElement("span");
    span.textContent = fund.name.replace(/ Direct (Plan )?Growth$/, "");
    label.appendChild(cb);
    label.appendChild(span);
    listEl.appendChild(label);

    cb.addEventListener("change", function () {
      enforceFundLimit();
      dismissFundWarnings();
      updateSelectAllState(listEl);
      if (_onFundSelectionChanged) _onFundSelectionChanged();
    });
  });
  enforceFundLimit();
  if (_onFundSelectionChanged) _onFundSelectionChanged();
}

function updateSelectAllState(listEl) {
  if (!listEl) return;
  var selectAllCb = listEl.querySelector(".fund-cb-select-all");
  var fundCbs = listEl.querySelectorAll(".fund-cb-fund");
  if (!selectAllCb || !fundCbs.length) return;
  var checked = 0;
  for (var i = 0; i < fundCbs.length; i++) {
    if (fundCbs[i].checked) checked++;
  }
  selectAllCb.checked = checked === fundCbs.length;
  selectAllCb.indeterminate = checked > 0 && checked < fundCbs.length;
}

function loadFundFilter() {
  var base = getApiBase();
  var listEl = document.getElementById("fund-checkbox-list");
  if (!listEl) return;

  fetch(base + "/funds")
    .then(function (res) { return res.ok ? res.json() : []; })
    .then(function (funds) {
      if (!funds || funds.length === 0) funds = _FALLBACK_FUNDS;
      _renderFundCheckboxes(funds, listEl);
    })
    .catch(function () {
      _renderFundCheckboxes(_FALLBACK_FUNDS, listEl);
    });
}

function enforceFundLimit() {
  // No cap on number of funds; all checkboxes remain enabled.
}

function dismissFundWarnings() {
  var ids = getSelectedFundIds();
  if (!ids || ids.length === 0) return;
  var msgs = document.querySelectorAll(".message.bot.refused");
  for (var i = 0; i < msgs.length; i++) {
    var txt = msgs[i].textContent || "";
    if (txt.indexOf("select at least one fund") !== -1 ||
        txt.indexOf("not selected in the filter") !== -1) {
      msgs[i].remove();
    }
  }
}

function getSelectedFundIds() {
  var listEl = document.getElementById("fund-checkbox-list");
  if (!listEl) return null;
  var cbs = listEl.querySelectorAll(".fund-cb-fund:checked");
  var ids = [];
  for (var i = 0; i < cbs.length; i++) {
    ids.push(cbs[i].value);
  }
  return ids.length > 0 ? ids : null;
}

/* ── Main app ── */

function runApp() {
  const messagesEl = document.getElementById("messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");
  const newChatBtn = document.getElementById("new-chat-btn");
  const selectionChip = document.getElementById("selection-chip");
  const selectionNames = document.getElementById("selection-names");
  const tipToast = document.getElementById("selection-tip-toast");
  const openFundsBtn = document.getElementById("open-funds-btn");
  const closeFundsBtn = document.getElementById("close-funds-btn");
  const mobileSheetBackdrop = document.getElementById("mobile-sheet-backdrop");

  function isMobileViewport() {
    return window.innerWidth <= 768;
  }

  function closeMobileFundSheet() {
    document.body.classList.remove("mobile-sheet-open");
    if (mobileSheetBackdrop) mobileSheetBackdrop.classList.add("hidden");
  }

  function openMobileFundSheet() {
    if (!isMobileViewport()) return;
    document.body.classList.add("mobile-sheet-open");
    if (mobileSheetBackdrop) mobileSheetBackdrop.classList.remove("hidden");
  }

  function updateFundButtonLabel(count) {
    if (!openFundsBtn) return;
    openFundsBtn.textContent = "Select funds (" + count + ")";
  }

  function updateSelectionStateUI() {
    var ids = getSelectedFundIds() || [];
    var names = getSelectedFundNames(ids);
    var count = ids.length;
    if (selectionChip) {
      selectionChip.textContent = "Selected: " + count;
      selectionChip.classList.toggle("zero", count === 0);
    }
    if (selectionNames) {
      renderSelectionNameChips(selectionNames, names);
    }
    if (input) {
      input.placeholder = "";
    }
    if (sendBtn) {
      // Keep send clickable so users get explicit feedback when no funds are selected.
      sendBtn.disabled = false;
      sendBtn.title = count === 0 ? "Select at least one fund." : "";
      sendBtn.classList.toggle("needs-fund", count === 0);
    }
    updateFundButtonLabel(count);
  }

  function showSelectionTipOnce() {
    if (!tipToast) return;
    if (localStorage.getItem("selection_tip_seen_v1") === "1") return;
    tipToast.classList.remove("hidden");
    localStorage.setItem("selection_tip_seen_v1", "1");
    setTimeout(function () {
      tipToast.classList.add("hidden");
    }, 4500);
  }

  _onFundSelectionChanged = updateSelectionStateUI;
  loadDataLastUpdated();
  loadFundFilter();
  updateSelectionStateUI();
  showSelectionTipOnce();

  if (openFundsBtn) {
    openFundsBtn.addEventListener("click", openMobileFundSheet);
  }
  if (closeFundsBtn) {
    closeFundsBtn.addEventListener("click", closeMobileFundSheet);
  }
  if (mobileSheetBackdrop) {
    mobileSheetBackdrop.addEventListener("click", closeMobileFundSheet);
  }
  window.addEventListener("resize", function () {
    if (!isMobileViewport()) {
      closeMobileFundSheet();
    }
  });

  function addMessage(role, content, options = {}) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    if (options.refused) div.classList.add("refused");
    if (options.rateLimit) div.classList.add("rate-limit");

    const contentEl = document.createElement("div");
    contentEl.className = "content";
    contentEl.textContent = content;
    div.appendChild(contentEl);

    if (options.answeredFor && options.answeredFor.length > 0) {
      const scope = document.createElement("p");
      scope.className = "answer-scope";
      scope.textContent = "Answered for: " + options.answeredFor.join(", ");
      div.appendChild(scope);
    }

    if (options.sources && options.sources.length > 0) {
      const title = document.createElement("p");
      title.className = "sources-title";
      title.textContent = "Sources:";
      div.appendChild(title);
      const list = document.createElement("ul");
      list.className = "sources";
      options.sources.forEach(function (s) {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = s.url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = s.label || s.url;
        li.appendChild(a);
        list.appendChild(li);
      });
      div.appendChild(list);
    }

    if (options.refusalReason) {
      const reason = document.createElement("p");
      reason.className = "refusal-reason";
      reason.textContent = options.refusalReason;
      div.appendChild(reason);
    }

    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setStatus(text, isError) {
    const existing = document.querySelector(".status");
    if (existing) existing.remove();
    const el = document.createElement("p");
    el.className = "status" + (isError ? " error" : "");
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function clearStatus() {
    const el = document.querySelector(".status");
    if (el) el.remove();
  }

  var _thinkingTimer = null;
  var _thinkingEl = null;

  function showThinking() {
    _thinkingEl = document.createElement("div");
    _thinkingEl.className = "message bot thinking";
    var dot = document.createElement("div");
    dot.className = "content thinking-content";
    dot.textContent = "Thinking...";
    _thinkingEl.appendChild(dot);
    messagesEl.appendChild(_thinkingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    var seconds = 0;
    _thinkingTimer = setInterval(function () {
      seconds++;
      dot.textContent = "Thinking... (" + seconds + "s)";
    }, 1000);
  }

  function hideThinking() {
    if (_thinkingTimer) { clearInterval(_thinkingTimer); _thinkingTimer = null; }
    if (_thinkingEl) { _thinkingEl.remove(); _thinkingEl = null; }
  }

  function setLoading(loading) {
    if (loading) {
      sendBtn.disabled = true;
    } else {
      updateSelectionStateUI();
    }
    input.disabled = loading;
  }

  function submitMessage(text) {
    const message = (text || "").trim();
    if (!message) return;

    var fundIds = getSelectedFundIds() || [];
    var mentioned = detectMentionedFundIds(message);

    // Use funds mentioned in the question if any; otherwise use selected funds.
    // This allows answering about a different fund than the one selected in the filter.
    var effectiveFundIds = [];
    if (mentioned.length > 0) {
      effectiveFundIds = mentioned;
    } else if (fundIds.length > 0) {
      effectiveFundIds = fundIds;
    }

    if (effectiveFundIds.length === 0) {
      addMessage("bot", "Please select at least one fund from the filter, or mention a fund in your question.", { refused: true });
      return;
    }

    var selectedNames = getSelectedFundNames(effectiveFundIds);

    addMessage("user", message);
    closeMobileFundSheet();
    input.value = "";
    setLoading(true);
    clearStatus();
    showThinking();

    var body = { message: message };
    if (effectiveFundIds) body.fund_ids = effectiveFundIds;

    const url = getApiBase() + "/chat";
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("Request failed: " + res.status);
        return res.json();
      })
      .then(function (data) {
        hideThinking();
        var answer = data.answer || "No answer.";
        var isRateLimit = answer.indexOf("free-tier limit") !== -1 || answer.indexOf("Please try again in a few minutes") !== -1;
        addMessage("bot", answer, {
          sources: data.sources || [],
          refused: data.refused === true,
          refusalReason: data.refusal_reason || null,
          rateLimit: isRateLimit,
          answeredFor: selectedNames,
        });
      })
      .catch(function (err) {
        hideThinking();
        setStatus("Error: " + (err.message || "Could not reach the server. Is the backend running?"), true);
      })
      .finally(function () {
        setLoading(false);
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    submitMessage(input.value);
  });

  if (newChatBtn) {
    newChatBtn.addEventListener("click", function () {
      messagesEl.innerHTML = "";
      clearStatus();
      input.value = "";
      input.focus();
    });
  }

  document.querySelectorAll(".example-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const query = this.getAttribute("data-query");
      if (query) submitMessage(query);
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", runApp);
} else {
  runApp();
}
