
// =====================
// Typing Effect for Subtitle
// =====================
const typingElement = document.getElementById("typing");
const text = [
  "Intelligent Battlefield Node",
  "AI Threat Classification",
  "Real-Time Tactical Support"
];
let index = 0;
let charIndex = 0;

function typeEffect() {
  if (charIndex < text[index].length) {
    typingElement.textContent += text[index].charAt(charIndex);
    charIndex++;
    setTimeout(typeEffect, 100);
  } else {
    setTimeout(eraseEffect, 2000);
  }
}

function eraseEffect() {
  if (charIndex > 0) {
    typingElement.textContent = text[index].substring(0, charIndex - 1);
    charIndex--;
    setTimeout(eraseEffect, 50);
  } else {
    index = (index + 1) % text.length;
    setTimeout(typeEffect, 500);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  typeEffect();
  updateClock(); // Start clock when DOM is ready
});

// =====================
// Clock
// =====================
function updateClock() {
  const now = new Date();
  document.getElementById("clock").textContent = now.toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();


// =====================
// Chart.js Prediction Graph
// =====================
const ctx = document.getElementById("predictionChart");
if (ctx) {
  new Chart(ctx, {
    type: "line",
    data: {
      labels: ["Now", "+5m", "+10m", "+15m", "+20m"],
      datasets: [
        {
          label: "Threat Probability (%)",
          data: [72, 80, 85, 70, 60],
          borderColor: "#00ffcc",
          borderWidth: 2,
          fill: true,
          backgroundColor: "rgba(0, 255, 204, 0.1)",
          tension: 0.4
        }
      ]
    },
    options: {
      responsive: true,
      plugins: { 
        legend: { labels: { color: "#fff" } } 
      },
      scales: {
        x: { ticks: { color: "#fff" }, grid: { color: "rgba(255,255,255,0.1)" } },
        y: { ticks: { color: "#fff" }, grid: { color: "rgba(255,255,255,0.1)" } }
      }
    }
  });
}


// =====================
// Dashboard Card Animations
// =====================
const cards = document.querySelectorAll(".card");
cards.forEach(card => {
  card.addEventListener("mouseover", () => {
    card.style.transform = "translateY(-8px) scale(1.02)";
    card.style.boxShadow = "0 0 30px rgba(0, 255, 255, 0.5)";
  });
  card.addEventListener("mouseleave", () => {
    card.style.transform = "translateY(0) scale(1)";
    card.style.boxShadow = "0 0 20px rgba(0, 255, 255, 0.2)";
  });
});
