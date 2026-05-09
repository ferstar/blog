function css(name) {
  return "rgb(" + getComputedStyle(document.documentElement).getPropertyValue(name) + ")";
}

function initMermaidLight() {
  mermaid.initialize({
    theme: "base",
    themeVariables: {
      background: css("--color-neutral"),
      primaryColor: css("--color-primary-200"),
      secondaryColor: css("--color-secondary-200"),
      tertiaryColor: css("--color-neutral-100"),
      primaryBorderColor: css("--color-primary-400"),
      secondaryBorderColor: css("--color-secondary-400"),
      tertiaryBorderColor: css("--color-neutral-400"),
      lineColor: css("--color-neutral-600"),
      fontFamily:
        "ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,segoe ui,Roboto,helvetica neue,Arial,noto sans,sans-serif",
      fontSize: "16px",
    },
  });
}

function initMermaidDark() {
  mermaid.initialize({
    theme: "dark",
    themeVariables: {
      fontFamily:
        "ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,segoe ui,Roboto,helvetica neue,Arial,noto sans,sans-serif",
      fontSize: "16px",
    },
  });
}

function renderPendingMermaid() {
  if (typeof mermaid === "undefined") {
    return;
  }

  const pending = Array.from(document.querySelectorAll("pre.mermaid")).some(
    (element) => !element.getAttribute("data-processed"),
  );
  if (!pending) {
    return;
  }

  if (typeof updateMermaidTheme === "function") {
    updateMermaidTheme();
    return;
  }

  if (document.documentElement.classList.contains("dark")) {
    initMermaidDark();
  } else {
    initMermaidLight();
  }
  mermaid.run();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", renderPendingMermaid, { once: true });
} else {
  renderPendingMermaid();
}
