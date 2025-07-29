document.getElementById("start").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "start" });
});

document.getElementById("stop").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "stop" });
});
