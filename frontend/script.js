// ============================================================
//  script.js — QuickKart Frontend
//  Slider + horizontal scroll (unchanged) +
//  API-connected complaint chatbot (rewritten)
// ============================================================

const API_BASE = "http://127.0.0.1:8000";

// ─── Slider ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {

    const imgs     = document.querySelectorAll('.header-slider ul img');
    const prev_btn = document.querySelector('.control_prev');
    const next_btn = document.querySelector('.control_next');

    let n = 0;

    function changeSlide() {
        imgs.forEach(img => img.style.display = 'none');
        if (imgs[n]) imgs[n].style.display = 'block';
    }

    changeSlide();

    if (prev_btn) {
        prev_btn.addEventListener('click', (e) => {
            e.preventDefault();
            n = (n > 0) ? n - 1 : imgs.length - 1;
            changeSlide();
        });
    }

    if (next_btn) {
        next_btn.addEventListener('click', (e) => {
            e.preventDefault();
            n = (n < imgs.length - 1) ? n + 1 : 0;
            changeSlide();
        });
    }

    // ─── Horizontal scroll ──────────────────────────────────
    document.querySelectorAll('.products').forEach(container => {
        container.addEventListener('wheel', (evt) => {
            evt.preventDefault();
            container.scrollLeft += evt.deltaY;
        });
    });

});

// ─── Chatbot open / close ────────────────────────────────────
const btn      = document.getElementById("chatbot-btn");
const box      = document.getElementById("chatbot-box");
const closeBtn = document.getElementById("close-chat");

btn.onclick      = () => box.style.display = "flex";
closeBtn.onclick = () => box.style.display = "none";

// ─── Chat helpers ────────────────────────────────────────────

function appendMsg(text, className) {
    const chatBody = document.getElementById("chat-body");
    const div      = document.createElement("div");
    div.className  = className;
    div.innerHTML  = text;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
    return div;
}

function riskBadge(level) {
    const colors = {
        Critical: "#c0392b",
        High:     "#e67e22",
        Medium:   "#f1c40f",
        Low:      "#27ae60"
    };
    const bg = colors[level] || "#7f8c8d";
    return `<span style="
        background:${bg};
        color:#fff;
        padding:2px 8px;
        border-radius:12px;
        font-size:12px;
        font-weight:600;
        margin-left:4px;
    ">${level}</span>`;
}

function typeBadge(type) {
    return `<span style="
        background:#2980b9;
        color:#fff;
        padding:2px 8px;
        border-radius:12px;
        font-size:12px;
        margin-left:4px;
    ">${type.replace(/_/g, " ")}</span>`;
}

function buildBotReply(data) {
    let reply = "";

    if (data.risk_level === "Critical") {
        reply = "We're sorry to hear this. Your complaint has been escalated to our senior support team and an agent will contact you within 2 hours.";
    } else if (data.risk_level === "High") {
        reply = "We apologize for the inconvenience. Your complaint has been assigned to a dedicated agent who will reach out within 4 hours.";
    } else if (data.risk_level === "Medium") {
        reply = "Thank you for reaching out. Your complaint has been registered and will be resolved within 48 hours. You will receive an update via email.";
    } else {
        reply = "Thank you for contacting QuickKart Support. Your complaint has been registered. Expected resolution time is 3 to 5 working days.";
    }

    return `<div style="line-height:1.7">${reply}</div>`;
}

// ─── Send message ─────────────────────────────────────────────

async function sendMessage() {
    const input   = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    appendMsg(message, "user-msg");
    input.value = "";

    // Handle non-complaint quick replies
    const lower = message.toLowerCase();
    if (lower.includes("hello") || lower.includes("hi")) {
        appendMsg("Hi! 👋 Welcome to QuickKart! Describe your complaint and I'll analyse it for you.", "bot-msg");
        return;
    }
    if (lower.includes("price")) {
        appendMsg("You can check prices on the product page 🛍️", "bot-msg");
        return;
    }
    if (lower.includes("contact")) {
        appendMsg("You can reach us at support@quickkart.com 📧", "bot-msg");
        return;
    }

    // Show typing indicator
    const typing = appendMsg("<i>Analysing your complaint…</i>", "bot-msg");

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                complaint_text: message,
                anger_score:    0.6,   // default; can wire to a slider later
                days_pending:   1,
                repeat_count:   1
            })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            typing.innerHTML = `⚠️ Error ${response.status}: ${err.detail || "Something went wrong."}`;
            return;
        }

        const data    = await response.json();
        typing.innerHTML = buildBotReply(data);

    } catch (e) {
        typing.innerHTML = "⚠️ Could not reach the server. Is the backend running?";
    }
}

// Allow Enter key to send
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("user-input");
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }
});
