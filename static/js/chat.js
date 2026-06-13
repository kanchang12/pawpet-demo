(function () {
  const launcher = document.getElementById("chat-launcher");
  const panel = document.getElementById("chat-panel");
  const messages = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const suggestions = document.getElementById("chat-suggestions");

  let history = []; // [{role: 'user'|'model', text: '...'}]

  function open() {
    panel.classList.add("open");
    input.focus();
  }

  launcher.addEventListener("click", () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) input.focus();
  });

  function addMessage(text, role) {
    const div = document.createElement("div");
    div.className = "msg " + (role === "user" ? "user" : "bot");
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage(text) {
    if (!text.trim()) return;
    addMessage(text, "user");
    history.push({ role: "user", text: text });
    input.value = "";

    const typing = document.createElement("div");
    typing.className = "msg bot";
    typing.textContent = "…";
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: history.slice(0, -1) }),
      });
      const data = await res.json();
      typing.remove();
      const reply = data.reply || "Sorry, something went wrong — please try again.";
      addMessage(reply, "model");
      history.push({ role: "model", text: reply });
    } catch (err) {
      typing.remove();
      addMessage("Sorry, I couldn't reach the assistant just now. Please try again.", "model");
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(input.value);
  });

  suggestions.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    open();
    sendMessage(chip.dataset.question);
  });

  document.querySelectorAll(".faq-item").forEach((item) => {
    item.addEventListener("click", () => {
      open();
      sendMessage(item.dataset.question);
    });
  });
})();
