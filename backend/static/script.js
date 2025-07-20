async function sendMessage() {
  const input = document.getElementById("userInput");
  const msg = input.value.trim();
  const chatbox = document.getElementById("chatbox");

  if (!msg) return;

  // Show user's message
  const userDiv = document.createElement("div");
  userDiv.className = "user";
  userDiv.textContent = `You: ${msg}`;
  chatbox.appendChild(userDiv);

  // Clear input and show typing...
  input.value = "";
  const typingDiv = document.createElement("div");
  typingDiv.className = "bubu";
  typingDiv.id = "typing";
  typingDiv.innerHTML = `Bubu 🧸: <span class="dots">...</span>`;
  chatbox.appendChild(typingDiv);
  chatbox.scrollTop = chatbox.scrollHeight;

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });

    const data = await res.json();
    document.getElementById("typing")?.remove();

    const replyDiv = document.createElement("div");
    replyDiv.className = "bubu";

    if (data.image_url) {
      replyDiv.innerHTML = `
        Bubu 🧸: <br>
        <img src='${data.image_url}' alt="Generated Image" width='300' style='border-radius:8px; margin-top:5px;'/>
        <br>
        <a href='${data.image_url}' download="bubu_image.png" title="Download Image" style="text-decoration:none; font-size:20px;">⬇️ Download Image</a>
      `;
    } else {
      replyDiv.innerHTML = `Bubu 🧸: ${data.reply || data.error || "❌ Something went wrong."}`;
    }

    chatbox.appendChild(replyDiv);
  } catch (error) {
    document.getElementById("typing")?.remove();
    const errorDiv = document.createElement("div");
    errorDiv.className = "bubu error";
    errorDiv.textContent = `Bubu 🧸: [Error] ${error.message}`;
    chatbox.appendChild(errorDiv);
  }

  chatbox.scrollTop = chatbox.scrollHeight;
}

document.getElementById("userInput").addEventListener("keypress", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
    sendMessage();
  }
});

window.onload = () => {
  document.getElementById("userInput").focus();
};
