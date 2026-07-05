const messages = document.getElementById("messages");
const promptEl = document.getElementById("prompt");
const busy = document.getElementById("busy");
const sendBtn = document.getElementById("send");

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function addMessage(role, content, meta = "") {
  const div = document.createElement("div");
  div.className = "msg " + role;

  const imageMatch = String(content).match(/!\[[^\]]*\]\(([^)]+)\)/);
  const fileMatch = String(content).match(/File:\s*`([^`]+)`/);

  let html = `<div class="meta">${escapeHtml(meta || role)}</div>`;

  if (imageMatch) {
    const url = imageMatch[1];
    const cleaned = String(content).replace(/!$begin:math:display$\[\^$end:math:display$]*\]$begin:math:text$\[\^\)\]\+$end:math:text$/, "").trim();
    html += `<div>${escapeHtml(cleaned)}</div>`;
    html += `<img class="generated" src="${url}" alt="Generated image">`;
    html += `<div class="status" style="margin-top:8px"><a href="${url}" target="_blank">open image</a></div>`;
    if (fileMatch) {
      html += `<div class="status">Saved: ${escapeHtml(fileMatch[1])}</div>`;
    }
  } else {
    html += escapeHtml(content);
  }

  div.innerHTML = html;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function clearMessages() {
  messages.innerHTML = "";
}

async function checkHealth() {
  const h = document.getElementById("health");
  try {
    const res = await fetch("/health", { cache: "no-store" });
    const j = await res.json();
    h.innerHTML = `<span class="ok">online</span> · SyMoNeuRaL MoE`;
  } catch (e) {
    h.innerHTML = `<span class="err">offline</span>`;
  }
}

function normalizePromptForRouter(text) {
  const t = text.trim();

  // Do not force modes in UI. Just help obvious shorthand route correctly.
  if (/^(dragon|cat|dog|castle|car|logo|portrait|landscape)$/i.test(t)) {
    return "generate an image of " + t;
  }

  return t;
}

async function sendPrompt() {
  let prompt = normalizePromptForRouter(promptEl.value);
  if (!prompt) return;

  addMessage("user", prompt, "you");
  promptEl.value = "";
  busy.textContent = "SyMoNeuRaL is working...";
  sendBtn.disabled = true;

  try {
    const res = await fetch("/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify({
        model: "symoneural_moe",
        stream: false,
        messages: [{ role: "user", content: prompt }],
        max_tokens: 512
      })
    });

    const raw = await res.text();

    if (!res.ok) {
      throw new Error("HTTP " + res.status + "\\n" + raw);
    }

    const data = JSON.parse(raw);
    const content =
      data?.choices?.[0]?.message?.content ||
      data?.choices?.[0]?.text ||
      JSON.stringify(data, null, 2);

    const model = data?.model || "SyMoNeuRaL MoE";
    addMessage("assistant", content, model);
  } catch (e) {
    addMessage("assistant", e.message || String(e), "error");
  } finally {
    busy.textContent = "";
    sendBtn.disabled = false;
    promptEl.focus();
  }
}

promptEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendPrompt();
  }
});

checkHealth();
addMessage(
  "assistant",
  "Ask for code. Ask for images. Ask for the build. SyMoNeuRaL routes it and gets to work.\n\nThis ain’t AI. This is SyMoNeuRaL.",
  "SyMoNeuRaL MoE"
);
