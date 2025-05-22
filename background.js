chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url) {
    fetch("https://kidguard.onrender.com/report_website", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify({
        url: changeInfo.url,
        title: tab.title || "No Title",
        content: ""  // You can’t access full content without permissions; send empty for now
      })
    })
    .then(response => response.json())
    .then(data => console.log("Activity sent:", data))
    .catch(err => console.error("Failed to send activity:", err));
  }
});
