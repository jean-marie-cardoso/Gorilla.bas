(() => {
    "use strict";

    const MIN_GAME_RATIO = 1.6;
    const MAX_LOGICAL_WIDTH = 920;
    const LOGICAL_HEIGHT = 400;
    let resizeFrame = 0;
    let canvasRepairFrame = 0;
    let canvasRepairTimers = [];
    let viewportSignature = "";
    let viewportStableSince = 0;
    let installPrompt = null;
    let wakeLock = null;

    const root = document.documentElement;
    const body = document.body;

    function isStandalone() {
        return Boolean(
            window.matchMedia("(display-mode: fullscreen)").matches
            || window.matchMedia("(display-mode: standalone)").matches
            || window.navigator.standalone
        );
    }

    function isIPhone() {
        return /iPhone|iPod/i.test(window.navigator.userAgent);
    }

    function fullscreenElement() {
        return document.fullscreenElement || document.webkitFullscreenElement;
    }

    function readSafeArea() {
        let probe = document.getElementById("safe-area-probe");
        if (!probe) {
            probe = document.createElement("div");
            probe.id = "safe-area-probe";
            probe.setAttribute("aria-hidden", "true");
            body.appendChild(probe);
        }
        const style = window.getComputedStyle(probe);
        return {
            top: Number.parseFloat(style.paddingTop) || 0,
            right: Number.parseFloat(style.paddingRight) || 0,
            bottom: Number.parseFloat(style.paddingBottom) || 0,
            left: Number.parseFloat(style.paddingLeft) || 0,
        };
    }

    function syncViewport() {
        resizeFrame = 0;
        const viewport = window.visualViewport;
        const width = Math.max(1, viewport ? viewport.width : window.innerWidth);
        const height = Math.max(1, viewport ? viewport.height : window.innerHeight);
        const offsetLeft = viewport ? viewport.offsetLeft : 0;
        const offsetTop = viewport ? viewport.offsetTop : 0;
        const safe = readSafeArea();
        const safeWidth = Math.max(1, width - safe.left - safe.right);
        const safeHeight = Math.max(1, height - safe.top - safe.bottom);
        const nextSignature = [
            Math.round(safeWidth),
            Math.round(safeHeight),
            Math.round(offsetLeft),
            Math.round(offsetTop),
        ].join("x");
        if (nextSignature !== viewportSignature) {
            viewportSignature = nextSignature;
            viewportStableSince = window.performance.now();
        }

        const gameWidth = safeWidth;
        const gameHeight = safeHeight;
        const logicalWidth = Math.max(
            640,
            Math.min(
                MAX_LOGICAL_WIDTH,
                Math.round(
                    LOGICAL_HEIGHT * Math.max(MIN_GAME_RATIO, safeWidth / safeHeight) / 8,
                ) * 8,
            ),
        );
        window.GorillaViewport = {
            width: safeWidth,
            height: safeHeight,
            logicalWidth,
            logicalHeight: LOGICAL_HEIGHT,
            stableSince: viewportStableSince,
        };

        const values = {
            "--app-width": `${Math.round(width)}px`,
            "--app-height": `${Math.round(height)}px`,
            "--viewport-left": `${Math.round(offsetLeft)}px`,
            "--viewport-top": `${Math.round(offsetTop)}px`,
            "--safe-top": `${Math.round(safe.top)}px`,
            "--safe-right": `${Math.round(safe.right)}px`,
            "--safe-bottom": `${Math.round(safe.bottom)}px`,
            "--safe-left": `${Math.round(safe.left)}px`,
            "--safe-width": `${Math.round(safeWidth)}px`,
            "--safe-height": `${Math.round(safeHeight)}px`,
            "--game-width": `${Math.round(gameWidth)}px`,
            "--game-height": `${Math.round(gameHeight)}px`,
            "--game-center-x": `${Math.round(offsetLeft + safe.left + safeWidth / 2)}px`,
            "--game-center-y": `${Math.round(offsetTop + safe.top + safeHeight / 2)}px`,
        };
        for (const [name, value] of Object.entries(values)) {
            root.style.setProperty(name, value);
        }

        body.classList.toggle(
            "compact-landscape",
            width > height && (height <= 430 || width <= 700),
        );
        body.classList.toggle("is-standalone", isStandalone());
        scheduleCanvasRepair();
    }

    function scheduleViewportSync() {
        if (!resizeFrame) {
            resizeFrame = window.requestAnimationFrame(syncViewport);
        }
    }

    function repairCanvasBackingStore() {
        canvasRepairFrame = 0;
        const canvas = document.getElementById("canvas");
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        if (rect.width < 2 || rect.height < 2 || canvas.width < 2 || canvas.height < 2) {
            return;
        }

        const cssRatio = rect.width / rect.height;
        const backingRatio = canvas.width / canvas.height;
        const ratioError = Math.abs(cssRatio - backingRatio) / cssRatio;
        if (ratioError > 0.015) {
            const width = Math.max(2, Math.round(rect.width));
            const height = Math.max(2, Math.round(rect.height));
            if (typeof window.Module?.setCanvasSize === "function") {
                window.Module.setCanvasSize(width, height);
            } else if (typeof window.window_resize === "function") {
                window.window_resize();
            }
        }
    }

    function scheduleCanvasRepair() {
        if (!canvasRepairFrame) {
            canvasRepairFrame = window.requestAnimationFrame(() => {
                window.requestAnimationFrame(repairCanvasBackingStore);
            });
        }
        for (const timer of canvasRepairTimers) {
            window.clearTimeout(timer);
        }
        // Safari et Pygbag peuvent finir leur redimensionnement à des moments
        // différents. Quelques vérifications légères couvrent les deux.
        canvasRepairTimers = [220, 700, 1600, 3200].map((delay, index, delays) => (
            window.setTimeout(() => {
                repairCanvasBackingStore();
                if (index === delays.length - 1) {
                    canvasRepairTimers = [];
                }
            }, delay)
        ));
    }

    function updateFullscreenButton() {
        const button = document.getElementById("fullscreen-toggle");
        if (!button) return;
        const active = Boolean(fullscreenElement());
        const label = active ? "Quitter le plein écran" : "Plein écran";
        button.setAttribute("aria-label", label);
        button.title = label;
        const text = button.querySelector(".fullscreen-label");
        if (text) text.textContent = active ? "QUITTER" : "PLEIN ÉCRAN";
        button.classList.toggle("is-active", active);
        body.classList.toggle("is-fullscreen", active);
    }

    async function requestWakeLock() {
        if (!("wakeLock" in navigator) || document.visibilityState !== "visible") return;
        try {
            wakeLock = await navigator.wakeLock.request("screen");
        } catch (_) {
            wakeLock = null;
        }
    }

    async function lockLandscape() {
        try {
            if (screen.orientation && screen.orientation.lock) {
                await screen.orientation.lock("landscape");
            }
        } catch (_) {
            // Plusieurs navigateurs refusent le verrouillage : la rotation
            // manuelle reste toujours disponible.
        }
    }

    function showInstallHelp() {
        const dialog = document.getElementById("fullscreen-help");
        if (!dialog) return;
        dialog.hidden = false;
        document.getElementById("fullscreen-help-close")?.focus();
    }

    async function toggleFullscreen() {
        if (fullscreenElement()) {
            const exit = document.exitFullscreen || document.webkitExitFullscreen;
            if (exit) {
                try {
                    await exit.call(document);
                } catch (_) {}
            }
            return;
        }

        if (isStandalone()) {
            await lockLandscape();
            await requestWakeLock();
            return;
        }

        // Sur iPhone, l'ancien préfixe WebKit peut exister sans fonctionner
        // sur un élément HTML. On ne l'utilise que si l'API standard arrive.
        if (isIPhone() && !root.requestFullscreen) {
            showInstallHelp();
            return;
        }

        const request = root.requestFullscreen || root.webkitRequestFullscreen;
        if (request) {
            try {
                if (root.requestFullscreen) {
                    await request.call(root, { navigationUI: "hide" });
                } else {
                    await request.call(root);
                }
                await new Promise((resolve) => window.requestAnimationFrame(resolve));
                if (fullscreenElement()) {
                    await lockLandscape();
                    await requestWakeLock();
                    return;
                }
            } catch (_) {
                // Le bouton reste utile : on propose alors le mode application.
            }
        }

        if (installPrompt) {
            try {
                installPrompt.prompt();
                await installPrompt.userChoice;
                installPrompt = null;
                return;
            } catch (_) {}
        }
        showInstallHelp();
    }

    function createControls() {
        const button = document.createElement("button");
        button.id = "fullscreen-toggle";
        button.type = "button";
        button.innerHTML = `
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"/>
            </svg>
            <span class="fullscreen-label">PLEIN ÉCRAN</span>
        `;
        button.addEventListener("click", toggleFullscreen);
        button.addEventListener("pointerdown", (event) => event.stopPropagation());
        body.appendChild(button);

        const rotatePanel = document.getElementById("rotate-device");
        if (rotatePanel) {
            const rotateButton = document.createElement("button");
            rotateButton.id = "rotate-fullscreen";
            rotateButton.type = "button";
            rotateButton.textContent = "⛶  PLEIN ÉCRAN";
            rotateButton.addEventListener("click", toggleFullscreen);
            rotatePanel.appendChild(rotateButton);
        }

        const help = document.createElement("section");
        help.id = "fullscreen-help";
        help.hidden = true;
        help.setAttribute("role", "dialog");
        help.setAttribute("aria-modal", "true");
        help.setAttribute("aria-labelledby", "fullscreen-help-title");
        help.innerHTML = `
            <div class="fullscreen-help-card">
                <h2 id="fullscreen-help-title">Plein écran sur iPhone</h2>
                <p>
                    Safari iPhone ne permet pas encore le vrai plein écran
                    pour un jeu. Touche <strong>Partager</strong>, puis
                    <strong>Sur l’écran d’accueil</strong>. Ouvre ensuite
                    l’icône Gorillas : les barres Safari disparaîtront.
                </p>
                <button id="fullscreen-help-close" type="button">J’AI COMPRIS</button>
            </div>
        `;
        help.addEventListener("click", (event) => {
            if (event.target === help) help.hidden = true;
        });
        help.querySelector("#fullscreen-help-close").addEventListener("click", () => {
            help.hidden = true;
            button.focus();
        });
        body.appendChild(help);
        updateFullscreenButton();
    }

    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        installPrompt = event;
    });
    window.addEventListener("resize", scheduleViewportSync, { passive: true });
    window.addEventListener("orientationchange", scheduleViewportSync, { passive: true });
    window.addEventListener("pageshow", scheduleViewportSync, { passive: true });
    window.addEventListener("load", scheduleViewportSync, { once: true });
    document.addEventListener("fullscreenchange", () => {
        updateFullscreenButton();
        scheduleViewportSync();
    });
    document.addEventListener("webkitfullscreenchange", () => {
        updateFullscreenButton();
        scheduleViewportSync();
    });
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") {
            scheduleViewportSync();
            if (fullscreenElement() || isStandalone()) {
                requestWakeLock();
            }
        }
    });
    if (window.visualViewport) {
        window.visualViewport.addEventListener("resize", scheduleViewportSync, { passive: true });
        window.visualViewport.addEventListener("scroll", scheduleViewportSync, { passive: true });
    }

    createControls();
    syncViewport();
    if (isStandalone()) {
        lockLandscape();
        requestWakeLock();
    }

    if ("serviceWorker" in navigator && (
        window.location.protocol === "https:"
        || window.location.hostname === "localhost"
        || window.location.hostname === "127.0.0.1"
    )) {
        window.addEventListener("load", () => {
            navigator.serviceWorker.register("./sw.js").catch(() => {});
        }, { once: true });
    }

    window.GorillaMobileShell = {
        syncViewport,
        scheduleViewportSync,
        scheduleCanvasRepair,
        repairCanvasBackingStore,
        toggleFullscreen,
        showInstallHelp,
    };
})();
