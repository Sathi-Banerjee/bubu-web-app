// functon that help sending messages
async function sendMessage() {
  const input = document.getElementById("userInput");
  const msg = input.value;
  if (!msg.trim()) return;

  const chatbox = document.getElementById("chatbox");
  chatbox.innerHTML += `<div class='user'>You: ${msg}</div>`;
  input.value = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });

    const data = await res.json();
    chatbox.innerHTML += `<div class='bubu'>Bubu 🧸: ${data.reply}</div>`;
    chatbox.scrollTop = chatbox.scrollHeight;
  } catch (error) {
    chatbox.innerHTML += `<div class='bubu'>Bubu 🧸: [Error] ${error}</div>`;
  }
}

// Enter key
document.getElementById("userInput").addEventListener("keypress", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
    sendMessage();
  }
});
