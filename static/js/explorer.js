const copyFeedback = document.querySelector(".copy-feedback");
for (const button of document.querySelectorAll("[data-copy]")) {
  button.hidden = false;
  button.addEventListener("click", async () => {
    const code = document.getElementById(button.dataset.copy);
    try {
      await navigator.clipboard.writeText(code.textContent);
      copyFeedback.textContent = "SQL copied.";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(code);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      copyFeedback.textContent = "SQL selected. Press Ctrl+C or ⌘C to copy.";
    }
  });
}
