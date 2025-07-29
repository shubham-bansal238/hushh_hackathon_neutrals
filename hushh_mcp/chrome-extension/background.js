let monitoring = false;
let products = [];

// === Load product list from backend ===
async function loadProducts() {
  try {
    const response = await fetch("http://127.0.0.1:5000/groq_output.json");
    products = await response.json();
    console.log("📦 Products loaded:", products.length);
  } catch (err) {
    console.error("❌ Failed to load products:", err);
    products = [];
  }
}

// === Matching function ===
function matchTitleAgainstProducts(title) {
  const matches = [];
  const lowerTitle = title.toLowerCase();

  for (const product of products) {
    const allKeywords = [
      product.canonical_name.toLowerCase(),
      ...(product.aliases || []).map(a => a.toLowerCase()),
      ...(product.context_keywords || []).map(k => k.toLowerCase())
    ];

    for (const keyword of allKeywords) {
      if (lowerTitle.includes(keyword)) {
        console.log(`✅ Matched "${title}" by keyword "${keyword}" for product ${product.id}`);
        matches.push(product.id);
        break;
      }
    }
  }
  return matches;
}

// === Save results to backend ===
function saveResults(results) {
  fetch("http://127.0.0.1:5000/save-history", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(results)
  })
    .then(res => res.json())
    .then(data => console.log("✅ Results saved:", data))
    .catch(err => console.error("❌ Error saving:", err));
}

// === Monitoring handler ===
function startMonitoring() {
  if (monitoring) return;
  monitoring = true;
  console.log("▶️ Monitoring started...");

  chrome.tabs.onUpdated.addListener(tabListener);
}

function stopMonitoring() {
  if (!monitoring) return;
  monitoring = false;
  console.log("⏹️ Monitoring stopped.");

  chrome.tabs.onUpdated.removeListener(tabListener);
}

function tabListener(tabId, changeInfo, tab) {
  if (changeInfo.status === "complete" && tab.title) {
    const title = tab.title.trim();
    if (!title) return;

    const matchedProductIds = matchTitleAgainstProducts(title);
    if (matchedProductIds.length > 0) {
      const results = {};
      for (const productId of matchedProductIds) {
        results[productId] = {
          id: productId,
          matched_queries: [title]
        };
      }
      saveResults(results);
    }
  }
}

// === Listen for popup commands ===
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "start") startMonitoring();
  if (msg.action === "stop") stopMonitoring();
});

// === Load product list on startup ===
loadProducts();
