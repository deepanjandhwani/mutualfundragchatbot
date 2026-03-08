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

var MAX_FUND_SELECT = 3;

function loadFundFilter() {
  var base = getApiBase();
  var listEl = document.getElementById("fund-checkbox-list");
  if (!listEl) return;

  fetch(base + "/funds")
    .then(function (res) { return res.ok ? res.json() : []; })
    .then(function (funds) {
      listEl.innerHTML = "";
      funds.forEach(function (fund) {
        var label = document.createElement("label");
        label.className = "fund-checkbox";
        var cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "fund-cb";
        cb.value = fund.id;
        cb.checked = false;
        var span = document.createElement("span");
        span.textContent = fund.name.replace(/ Direct (Plan )?Growth$/, "");
        label.appendChild(cb);
        label.appendChild(span);
        listEl.appendChild(label);

        cb.addEventListener("change", function () {
          enforceFundLimit();
        });
      });
    })
    .catch(function () {
      listEl.innerHTML = '<span class="fund-filter-error">Could not load funds.</span>';
    });
}

function enforceFundLimit() {
  var listEl = document.getElementById("fund-checkbox-list");
  if (!listEl) return;
  var cbs = listEl.querySelectorAll(".fund-cb");
  var checkedCount = 0;
  for (var i = 0; i < cbs.length; i++) {
    if (cbs[i].checked) checkedCount++;
  }
  for (var i = 0; i < cbs.length; i++) {
    if (!cbs[i].checked) {
      cbs[i].disabled = checkedCount >= MAX_FUND_SELECT;
    }
  }
}

function getSelectedFundIds() {
  var listEl = document.getElementById("fund-checkbox-list");
  if (!listEl) return null;
  var cbs = listEl.querySelectorAll(".fund-cb:checked");
  var ids = [];
  for (var i = 0; i < cbs.length; i++) {
    ids.push(cbs[i].value);
  }
  return ids.length > 0 ? ids : null;
}

/* ── Main app ── */

function runApp() {
  loadDataLastUpdated();
  loadFundFilter();

  const messagesEl = document.getElementById("messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");
  const newChatBtn = document.getElementById("new-chat-btn");



  function addMessage(role, content, options = {}) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    if (options.refused) div.classList.add("refused");
    if (options.rateLimit) div.classList.add("rate-limit");

    const contentEl = document.createElement("div");
    contentEl.className = "content";
    contentEl.textContent = content;
    div.appendChild(contentEl);

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
    sendBtn.disabled = loading;
    input.disabled = loading;
  }

  function submitMessage(text) {
    const message = (text || "").trim();
    if (!message) return;

    var fundIds = getSelectedFundIds();
    if (!fundIds || fundIds.length === 0) {
      addMessage("bot", "Please select at least one fund (up to 3) from the filter.", { refused: true });
      return;
    }

    addMessage("user", message);
    input.value = "";
    setLoading(true);
    clearStatus();
    showThinking();

    var body = { message: message };
    if (fundIds) body.fund_ids = fundIds;

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
