document.addEventListener("DOMContentLoaded", () => {

    // ===== SLIDER =====
    const imgs = document.querySelectorAll('.header-slider ul img');
    const prev_btn = document.querySelector('.control_prev');
    const next_btn = document.querySelector('.control_next');

    let n = 0;

    function changeSlide() {
        imgs.forEach(img => img.style.display = 'none');
        imgs[n].style.display = 'block';
    }

    changeSlide();

    prev_btn.addEventListener('click', (e) => {
        e.preventDefault();
        n = (n > 0) ? n - 1 : imgs.length - 1;
        changeSlide();
    });

    next_btn.addEventListener('click', (e) => {
        e.preventDefault();
        n = (n < imgs.length - 1) ? n + 1 : 0;
        changeSlide();
    });

    // ===== HORIZONTAL SCROLL =====
    const scrollContainers = document.querySelectorAll('.products');

    scrollContainers.forEach(container => {
        container.addEventListener('wheel', (evt) => {
            evt.preventDefault();
            container.scrollLeft += evt.deltaY;
        });
    });

});



const btn = document.getElementById("chatbot-btn");
const box = document.getElementById("chatbot-box");
const closeBtn = document.getElementById("close-chat");

btn.onclick = () => box.style.display = "flex";
closeBtn.onclick = () => box.style.display = "none";

function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (message === "") return;

  const chatBody = document.getElementById("chat-body");

  // User message
  const userMsg = document.createElement("div");
  userMsg.className = "user-msg";
  userMsg.innerText = message;
  chatBody.appendChild(userMsg);

  // Bot reply
  const botMsg = document.createElement("div");
  botMsg.className = "bot-msg";

  let reply = "Sorry, I didn't understand 😅";

  if (message.toLowerCase().includes("hello")) {
    reply = "Hi! 👋 Welcome to QuickKart!";
  } 
  else if (message.toLowerCase().includes("price")) {
    reply = "You can check prices on the product page 🛍️";
  } 
  else if (message.toLowerCase().includes("return")) {
    reply = "We offer 7-day return policy ✅";
  } 
  else if (message.toLowerCase().includes("contact")) {
    reply = "You can contact us at support@quickkart.com 📧";
  }

  setTimeout(() => {
    botMsg.innerText = reply;
    chatBody.appendChild(botMsg);
    chatBody.scrollTop = chatBody.scrollHeight;
  }, 500);

  input.value = "";
}
