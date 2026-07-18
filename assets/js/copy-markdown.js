(() => {
  if (window.copyMarkdownInitialized) return;
  window.copyMarkdownInitialized = true;

  const copyText = async (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) throw new Error("Clipboard copy failed");
  };

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-markdown-url]");
    if (!button || button.disabled) return;

    const label = button.querySelector("[data-copy-markdown-label]");
    const originalLabel = button.dataset.copyLabel;
    button.disabled = true;

    try {
      const response = await fetch(button.dataset.copyMarkdownUrl, {
        headers: { Accept: "text/markdown" },
      });
      if (!response.ok) throw new Error(`Markdown request failed: ${response.status}`);
      await copyText(await response.text());
      label.textContent = button.dataset.copiedLabel;
      button.classList.add("copy-markdown-button-success");
    } catch (_error) {
      label.textContent = button.dataset.errorLabel;
      button.classList.add("copy-markdown-button-error");
    }

    window.setTimeout(() => {
      label.textContent = originalLabel;
      button.classList.remove("copy-markdown-button-success", "copy-markdown-button-error");
      button.disabled = false;
    }, 1800);
  });
})();
