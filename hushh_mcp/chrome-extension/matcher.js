async function loadProducts() {
  const response = await fetch(chrome.runtime.getURL("../jsons/groq_output.json"));
  return response.json();
}

function matchHistoryEntry(entry, products) {
  const matches = [];

  for (const product of products) {
    const allKeywords = [
      product.canonical_name.toLowerCase(),
      ...(product.aliases || []).map(a => a.toLowerCase()),
      ...(product.context_keywords || []).map(k => k.toLowerCase())
    ];

    const text = (entry.title + " " + entry.url).toLowerCase();

    if (allKeywords.some(keyword => text.includes(keyword))) {
      matches.push(product.id);
    }
  }

  return matches;
}

export { loadProducts, matchHistoryEntry };
// This code is part of a Chrome extension that matches browser history entries with product data.