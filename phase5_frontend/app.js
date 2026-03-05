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
  return (typeof API_BASE_URL !== "undefined" && API_BASE_URL) ? API_BASE_URL : "";
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

function runApp() {
  loadDataLastUpdated();

  const messagesEl = document.getElementById("messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");

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

  function setLoading(loading) {
    sendBtn.disabled = loading;
    input.disabled = loading;
  }

  function submitMessage(text) {
    const message = (text || "").trim();
    if (!message) return;

    addMessage("user", message);
    input.value = "";
    setLoading(true);
    clearStatus();

    const url = getApiBase() + "/chat";
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("Request failed: " + res.status);
        return res.json();
      })
      .then(function (data) {
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
