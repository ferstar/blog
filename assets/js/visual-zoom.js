(function () {
  "use strict";

  var IMAGE_SELECTOR = ".article-content img:not(.nozoom)";
  var MERMAID_SELECTOR = ".article-content pre.mermaid svg";
  var MAX_SCALE = 8;
  var MIN_SCALE = 0.35;
  var ZOOM_STEP = 1.22;
  var observerTimer = 0;

  var state = {
    modal: null,
    stage: null,
    content: null,
    caption: null,
    scale: 1,
    x: 0,
    y: 0,
    dragging: false,
    startX: 0,
    startY: 0,
    startPanX: 0,
    startPanY: 0,
    pointers: new Map(),
    pinchDistance: 0,
  };

  function icon(path) {
    return (
      '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
      '<path d="' +
      path +
      '"></path></svg>'
    );
  }

  var icons = {
    open: icon("M8 3H3v5h2V6.41l4.29 4.3 1.42-1.42L6.41 5H8V3Zm8 0v2h1.59l-4.3 4.29 1.42 1.42 4.29-4.3V8h2V3h-5ZM5 15.59V14H3v5h5v-2H6.41l4.3-4.29-1.42-1.42L5 15.59ZM19 17.59l-4.29-4.3-1.42 1.42 4.3 4.29H16v2h5v-5h-2v1.59Z"),
    zoomIn: icon("M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6V5Z"),
    zoomOut: icon("M5 11h14v2H5v-2Z"),
    reset: icon("M12 5a7 7 0 1 0 6.32 4H16a5 5 0 1 1-1.46-1.54L12 10h7V3l-3.03 3.03A6.97 6.97 0 0 0 12 5Z"),
    close: icon("m6.4 5 5.6 5.6L17.6 5 19 6.4 13.4 12l5.6 5.6-1.4 1.4-5.6-5.6L6.4 19 5 17.6l5.6-5.6L5 6.4 6.4 5Z"),
  };

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  }

  function button(label, html, onClick) {
    var el = document.createElement("button");
    el.type = "button";
    el.className = "visual-zoom-button";
    el.setAttribute("aria-label", label);
    el.title = label;
    el.innerHTML = html;
    el.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      onClick(event);
    });
    return el;
  }

  function ensureModal() {
    if (state.modal) return;

    var modal = document.createElement("div");
    modal.className = "visual-zoom-modal";
    modal.hidden = true;
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", "Media viewer");

    var toolbar = document.createElement("div");
    toolbar.className = "visual-zoom-toolbar";
    toolbar.appendChild(button("Zoom in", icons.zoomIn, function () { zoomFromCenter(ZOOM_STEP); }));
    toolbar.appendChild(button("Zoom out", icons.zoomOut, function () { zoomFromCenter(1 / ZOOM_STEP); }));
    toolbar.appendChild(button("Reset zoom", icons.reset, resetView));
    toolbar.appendChild(button("Close", icons.close, closeViewer));

    var stage = document.createElement("div");
    stage.className = "visual-zoom-stage";
    stage.tabIndex = -1;

    var content = document.createElement("div");
    content.className = "visual-zoom-content";
    stage.appendChild(content);

    var caption = document.createElement("div");
    caption.className = "visual-zoom-caption";

    modal.appendChild(toolbar);
    modal.appendChild(stage);
    modal.appendChild(caption);
    document.body.appendChild(modal);

    state.modal = modal;
    state.stage = stage;
    state.content = content;
    state.caption = caption;

    stage.addEventListener("wheel", onWheel, { passive: false });
    stage.addEventListener("pointerdown", onPointerDown);
    stage.addEventListener("pointermove", onPointerMove);
    stage.addEventListener("pointerup", onPointerEnd);
    stage.addEventListener("pointercancel", onPointerEnd);
    document.addEventListener("keydown", onKeyDown);
  }

  function mediaCaption(source) {
    var figure = source.closest("figure");
    var figcaption = figure ? figure.querySelector("figcaption") : null;
    if (figcaption && figcaption.textContent.trim()) return figcaption.textContent.trim();
    if (source.getAttribute("alt")) return source.getAttribute("alt");
    return "";
  }

  function imageSource(img) {
    var link = img.closest("a");
    return img.getAttribute("data-zoom-src") || (link && link.href) || img.currentSrc || img.src;
  }

  function serializeSvg(svg) {
    var clone = svg.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    var rect = svg.getBoundingClientRect();

    if (!clone.getAttribute("viewBox")) {
      var width = parseFloat(clone.getAttribute("width")) || rect.width;
      var height = parseFloat(clone.getAttribute("height")) || rect.height;
      if (width && height) clone.setAttribute("viewBox", "0 0 " + width + " " + height);
    }

    var viewBox = clone.getAttribute("viewBox");
    var parts = viewBox ? viewBox.split(/\s+/).map(parseFloat) : [];
    var viewBoxWidth = parts.length === 4 ? parts[2] : 0;
    var viewBoxHeight = parts.length === 4 ? parts[3] : 0;
    var finalWidth = Math.round(rect.width || viewBoxWidth);
    var finalHeight = Math.round(rect.height || viewBoxHeight);
    if (finalWidth && finalHeight) {
      clone.setAttribute("width", String(finalWidth));
      clone.setAttribute("height", String(finalHeight));
      clone.style.maxWidth = "none";
    }

    return new XMLSerializer().serializeToString(clone);
  }

  function openImage(img) {
    var media = document.createElement("img");
    media.src = imageSource(img);
    media.alt = img.getAttribute("alt") || "";
    media.decoding = "async";
    media.draggable = false;
    openViewer(media, mediaCaption(img));
  }

  function openMermaid(pre) {
    var svg = pre.querySelector("svg");
    if (!svg) return;

    var media = document.createElement("img");
    media.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(serializeSvg(svg));
    media.alt = "Mermaid diagram";
    media.draggable = false;
    openViewer(media, "");
  }

  function openViewer(media, captionText) {
    ensureModal();
    state.content.replaceChildren(media);
    state.caption.textContent = captionText || "";
    state.caption.hidden = !captionText;
    state.modal.hidden = false;
    document.documentElement.classList.add("visual-zoom-lock");
    resetView();
    state.stage.focus && state.stage.focus();
  }

  function closeViewer() {
    if (!state.modal || state.modal.hidden) return;
    state.modal.hidden = true;
    state.content.replaceChildren();
    state.pointers.clear();
    state.dragging = false;
    document.documentElement.classList.remove("visual-zoom-lock");
  }

  function resetView() {
    state.scale = 1;
    state.x = 0;
    state.y = 0;
    applyTransform();
  }

  function applyTransform() {
    state.content.style.transform =
      "translate3d(" + state.x + "px, " + state.y + "px, 0) scale(" + state.scale + ")";
  }

  function clampScale(scale) {
    return Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale));
  }

  function zoomAt(clientX, clientY, factor) {
    var rect = state.stage.getBoundingClientRect();
    var oldScale = state.scale;
    var nextScale = clampScale(oldScale * factor);
    if (nextScale === oldScale) return;

    var cx = clientX - rect.left - rect.width / 2;
    var cy = clientY - rect.top - rect.height / 2;
    state.x = cx - ((cx - state.x) / oldScale) * nextScale;
    state.y = cy - ((cy - state.y) / oldScale) * nextScale;
    state.scale = nextScale;
    applyTransform();
  }

  function zoomFromCenter(factor) {
    var rect = state.stage.getBoundingClientRect();
    zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, factor);
  }

  function onWheel(event) {
    if (!state.modal || state.modal.hidden) return;
    event.preventDefault();
    zoomAt(event.clientX, event.clientY, event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP);
  }

  function pointerDistance() {
    var points = Array.from(state.pointers.values());
    if (points.length < 2) return 0;
    var dx = points[0].clientX - points[1].clientX;
    var dy = points[0].clientY - points[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function pointerCenter() {
    var points = Array.from(state.pointers.values());
    return {
      x: (points[0].clientX + points[1].clientX) / 2,
      y: (points[0].clientY + points[1].clientY) / 2,
    };
  }

  function onPointerDown(event) {
    if (event.target.closest(".visual-zoom-toolbar")) return;
    state.stage.setPointerCapture(event.pointerId);
    state.pointers.set(event.pointerId, event);

    if (state.pointers.size === 2) {
      state.pinchDistance = pointerDistance();
      state.dragging = false;
      return;
    }

    state.dragging = true;
    state.stage.classList.add("is-dragging");
    state.startX = event.clientX;
    state.startY = event.clientY;
    state.startPanX = state.x;
    state.startPanY = state.y;
  }

  function onPointerMove(event) {
    if (!state.pointers.has(event.pointerId)) return;
    state.pointers.set(event.pointerId, event);

    if (state.pointers.size === 2) {
      var distance = pointerDistance();
      if (state.pinchDistance && distance) {
        var center = pointerCenter();
        zoomAt(center.x, center.y, distance / state.pinchDistance);
      }
      state.pinchDistance = distance;
      return;
    }

    if (!state.dragging) return;
    state.x = state.startPanX + event.clientX - state.startX;
    state.y = state.startPanY + event.clientY - state.startY;
    applyTransform();
  }

  function onPointerEnd(event) {
    state.pointers.delete(event.pointerId);
    state.pinchDistance = 0;
    if (state.pointers.size === 0) {
      state.dragging = false;
      state.stage.classList.remove("is-dragging");
    }
  }

  function onKeyDown(event) {
    if (!state.modal || state.modal.hidden) return;
    if (event.key === "Escape") closeViewer();
    if (event.key === "+" || event.key === "=") zoomFromCenter(ZOOM_STEP);
    if (event.key === "-") zoomFromCenter(1 / ZOOM_STEP);
    if (event.key === "0") resetView();
    if (event.key === "ArrowLeft") {
      state.x += 42;
      applyTransform();
    }
    if (event.key === "ArrowRight") {
      state.x -= 42;
      applyTransform();
    }
    if (event.key === "ArrowUp") {
      state.y += 42;
      applyTransform();
    }
    if (event.key === "ArrowDown") {
      state.y -= 42;
      applyTransform();
    }
  }

  function hostForMedia(el) {
    var figure = el.closest("figure");
    if (figure) return figure;

    var link = el.closest("a");
    if (link) {
      if (link.parentElement && !link.parentElement.classList.contains("article-content")) {
        return link.parentElement;
      }
      return wrapHost(link);
    }

    if (!el.parentElement || el.parentElement.classList.contains("article-content")) {
      return wrapHost(el);
    }

    return el.closest("p") || el.parentElement;
  }

  function wrapHost(el) {
    if (el.parentElement && el.parentElement.classList.contains("visual-zoom-inline-host")) {
      return el.parentElement;
    }

    var host = document.createElement("span");
    host.className = "visual-zoom-inline-host";
    el.parentNode.insertBefore(host, el);
    host.appendChild(el);
    return host;
  }

  function installTrigger(host, open) {
    if (!host || host.querySelector(":scope > .visual-zoom-trigger")) return;
    host.classList.add("visual-zoom-host");
    host.appendChild(button("Open media viewer", icons.open, open)).classList.add("visual-zoom-trigger");
  }

  function enhanceImage(img) {
    if (img.dataset.visualZoomReady === "true") return;
    img.dataset.visualZoomReady = "true";
    img.classList.add("visual-zoom-ready");
    img.title = img.title || "Open media viewer";

    if (!img.closest("a")) {
      img.setAttribute("role", "button");
      img.setAttribute("tabindex", "0");
      img.setAttribute("aria-label", "Open media viewer");
    }

    img.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      openImage(img);
    });
    img.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openImage(img);
      }
    });

    installTrigger(hostForMedia(img), function () { openImage(img); });
  }

  function enhanceMermaid(svg) {
    var pre = svg.closest("pre.mermaid");
    if (!pre) return;

    if (pre.dataset.visualZoomReady !== "true") {
      pre.dataset.visualZoomReady = "true";
      pre.classList.add("visual-zoom-ready");
      pre.setAttribute("role", "button");
      pre.setAttribute("tabindex", "0");
      pre.setAttribute("aria-label", "Open diagram viewer");
      pre.title = "Open diagram viewer";
      pre.addEventListener("click", function (event) {
        if (event.target.closest(".visual-zoom-trigger")) return;
        openMermaid(pre);
      });
      pre.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openMermaid(pre);
        }
      });
    }

    installTrigger(pre, function () { openMermaid(pre); });
  }

  function enhanceAll(root) {
    var scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll(IMAGE_SELECTOR).forEach(enhanceImage);
    scope.querySelectorAll(MERMAID_SELECTOR).forEach(enhanceMermaid);
  }

  function scheduleEnhance() {
    window.clearTimeout(observerTimer);
    observerTimer = window.setTimeout(function () { enhanceAll(document); }, 80);
  }

  ready(function () {
    enhanceAll(document);
    window.addEventListener("load", function () { enhanceAll(document); });
    new MutationObserver(scheduleEnhance).observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
})();
