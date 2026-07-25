# browser_input.py — champ HTML pour clavier mobile dans Pygbag
import json


class BrowserTextInput:
    """Champ HTML utilise par les navigateurs mobiles pour afficher le clavier."""

    def __init__(self):
        self.available = self._ensure()

    def _eval(self, code):
        try:
            import platform

            if hasattr(platform, "window"):
                return platform.window.eval(code)
        except Exception:
            return None
        return None

    def _ensure(self):
        code = r"""
(() => {
  if (window.GorillaMobileInput) {
    return true;
  }

  const state = {
    value: "",
    submitted: false,
    cancelled: false
  };

  const panel = document.createElement("div");
  panel.id = "gorilla-mobile-input-panel";
  panel.style.cssText = [
    "position:fixed",
    "left:50%",
    "bottom:calc(14px + env(safe-area-inset-bottom))",
    "transform:translateX(-50%)",
    "z-index:800",
    "display:none",
    "align-items:center",
    "gap:8px",
    "box-sizing:border-box",
    "width:min(92vw, 430px)",
    "padding:8px",
    "border:1px solid rgba(255,255,255,.35)",
    "border-radius:8px",
    "background:rgba(3,18,30,.94)",
    "box-shadow:0 10px 28px rgba(0,0,0,.35)"
  ].join(";");

  const input = document.createElement("input");
  input.id = "gorilla-mobile-text-input";
  input.type = "text";
  input.autocomplete = "off";
  input.autocorrect = "off";
  input.autocapitalize = "off";
  input.spellcheck = false;
  input.style.cssText = [
    "flex:1 1 auto",
    "min-width:0",
    "height:46px",
    "box-sizing:border-box",
    "border:0",
    "border-radius:6px",
    "padding:0 12px",
    "font:700 22px system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
    "letter-spacing:0",
    "color:#06111d",
    "background:#ffffff",
    "outline:2px solid transparent"
  ].join(";");

  const ok = document.createElement("button");
  ok.type = "button";
  ok.textContent = "OK";
  ok.style.cssText = [
    "flex:0 0 auto",
    "height:46px",
    "min-width:64px",
    "box-sizing:border-box",
    "border:0",
    "border-radius:6px",
    "padding:0 14px",
    "font:800 18px system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
    "letter-spacing:0",
    "color:#06111d",
    "background:#ffbd3f",
    "touch-action:manipulation"
  ].join(";");

  panel.appendChild(input);
  panel.appendChild(ok);
  document.body.appendChild(panel);

  const applyPosition = (position) => {
    const topRight = position === "top-right";
    const portrait = window.innerHeight > window.innerWidth;
    panel.style.left = topRight ? "auto" : "50%";
    panel.style.right = topRight ? "calc(8px + env(safe-area-inset-right))" : "auto";
    panel.style.top = topRight ? "calc(8px + env(safe-area-inset-top))" : "auto";
    panel.style.bottom = topRight ? "auto" : "calc(14px + env(safe-area-inset-bottom))";
    panel.style.transform = topRight ? "none" : "translateX(-50%)";
    panel.style.width = topRight
      ? (portrait ? "min(54vw, 205px)" : "clamp(170px, 28vw, 250px)")
      : "min(92vw, 430px)";
    panel.style.gap = topRight ? "4px" : "8px";
    panel.style.padding = topRight ? "4px" : "8px";
    input.style.height = topRight ? "34px" : "46px";
    input.style.padding = topRight ? "0 8px" : "0 12px";
    input.style.fontSize = topRight ? "15px" : "22px";
    ok.style.height = topRight ? "34px" : "46px";
    ok.style.minWidth = topRight ? "43px" : "64px";
    ok.style.padding = topRight ? "0 8px" : "0 14px";
    ok.style.fontSize = topRight ? "15px" : "18px";
  };

  const stopForGame = (event) => event.stopPropagation();
  [
    "keydown", "keyup", "keypress", "beforeinput", "input",
    "compositionstart", "compositionupdate", "compositionend",
    "pointerdown", "pointerup", "mousedown", "mouseup",
    "touchstart", "touchend"
  ].forEach((name) => {
    panel.addEventListener(name, stopForGame);
    input.addEventListener(name, stopForGame);
    ok.addEventListener(name, stopForGame);
  });

  const submit = () => {
    state.value = input.value;
    state.submitted = true;
  };

  input.addEventListener("input", () => {
    state.value = input.value;
  }, true);

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      submit();
    } else if (event.key === "Escape") {
      state.cancelled = true;
    }
  }, true);

  ok.addEventListener("click", (event) => {
    event.preventDefault();
    submit();
    input.focus({ preventScroll: true });
  }, true);

  window.GorillaMobileInput = {
    show(label, value, enterHint, inputMode, pattern, position) {
      state.value = value || "";
      state.submitted = false;
      state.cancelled = false;
      input.value = state.value;
      input.placeholder = label || "";
      input.enterKeyHint = enterHint || "done";
      input.inputMode = inputMode || "text";
      input.pattern = pattern || "";
      applyPosition(position || "bottom");
      panel.style.display = "flex";
      window.requestAnimationFrame(() => {
        input.focus({ preventScroll: true });
      });
    },
    hide() {
      panel.style.display = "none";
      input.blur();
      state.submitted = false;
      state.cancelled = false;
    },
    focus() {
      input.focus({ preventScroll: true });
    },
    value() {
      return input.value || "";
    },
    submitted() {
      const wasSubmitted = state.submitted;
      state.submitted = false;
      return wasSubmitted;
    },
    cancelled() {
      const wasCancelled = state.cancelled;
      state.cancelled = false;
      return wasCancelled;
    }
  };

  return true;
})()
"""
        return bool(self._eval(code))

    def show(self, label, value="", enter_hint="done", input_mode="text", pattern="", position="bottom"):
        if self.available:
            self._eval(
                "window.GorillaMobileInput.show(%s, %s, %s, %s, %s, %s)"
                % (
                    json.dumps(label),
                    json.dumps(value),
                    json.dumps(enter_hint),
                    json.dumps(input_mode),
                    json.dumps(pattern),
                    json.dumps(position),
                )
            )

    def hide(self):
        if self.available:
            self._eval("window.GorillaMobileInput.hide()")

    def focus(self):
        if self.available:
            self._eval("window.GorillaMobileInput.focus()")

    def value(self):
        if not self.available:
            return ""
        value = self._eval("window.GorillaMobileInput.value()")
        return "" if value is None else str(value)

    def submitted(self):
        return bool(self.available and self._eval("window.GorillaMobileInput.submitted()"))

    def cancelled(self):
        return bool(self.available and self._eval("window.GorillaMobileInput.cancelled()"))


class BrowserAimControls:
    """Deux curseurs HTML et un bouton de tir pour la version web.

    L'API reste muette sur ordinateur classique: ``available`` vaut alors
    ``False`` et l'interface Pygame prend le relais.
    """

    MIN_ANGLE = 5.0
    MAX_ANGLE = 85.0
    MIN_POWER = 50.0
    MAX_POWER = 400.0

    def __init__(self):
        self.available = self._ensure()

    def _eval(self, code):
        try:
            import platform

            if hasattr(platform, "window"):
                return platform.window.eval(code)
        except Exception:
            return None
        return None

    def _ensure(self):
        code = r"""
(() => {
  if (window.GorillaAimControls) {
    return true;
  }

  const state = { fired: false, moveRequested: false, cancelled: false };
  const panel = document.createElement("section");
  panel.id = "gorilla-aim-controls";
  panel.setAttribute("aria-label", "Réglage du tir");
  panel.style.cssText = [
    "position:fixed",
    "left:50%",
    "bottom:calc(10px + env(safe-area-inset-bottom))",
    "transform:translateX(-50%)",
    "z-index:800",
    "display:none",
    "align-items:center",
    "justify-content:center",
    "gap:12px",
    "box-sizing:border-box",
    "width:min(calc(100vw - env(safe-area-inset-left) - env(safe-area-inset-right) - 12px), 660px)",
    "max-width:calc(100vw - env(safe-area-inset-left) - env(safe-area-inset-right) - 12px)",
    "padding:10px 12px",
    "border:1px solid rgba(255,209,90,.55)",
    "border-radius:14px",
    "background:rgba(5,16,34,.94)",
    "box-shadow:0 12px 34px rgba(0,0,0,.42)",
    "color:#fff",
    "font:700 14px system-ui,-apple-system,BlinkMacSystemFont,sans-serif",
    "backdrop-filter:blur(8px)",
    "-webkit-backdrop-filter:blur(8px)"
  ].join(";");

  const makeRange = (labelText, min, max, step) => {
    const group = document.createElement("label");
    group.style.cssText = [
      "display:grid",
      "grid-template-columns:auto minmax(100px,1fr) 54px",
      "align-items:center",
      "gap:7px",
      "flex:1 1 210px",
      "min-width:0"
    ].join(";");

    const label = document.createElement("span");
    label.textContent = labelText;
    label.style.cssText = "white-space:nowrap;color:#ffd15a";

    const input = document.createElement("input");
    input.type = "range";
    input.min = String(min);
    input.max = String(max);
    input.step = String(step);
    input.setAttribute("aria-label", labelText);
    input.style.cssText = [
      "width:100%",
      "height:34px",
      "margin:0",
      "accent-color:#ffd15a",
      "cursor:pointer",
      "touch-action:none"
    ].join(";");

    const output = document.createElement("output");
    output.style.cssText = [
      "display:inline-flex",
      "justify-content:center",
      "align-items:center",
      "height:30px",
      "border-radius:7px",
      "background:#142849",
      "color:#fff",
      "font-variant-numeric:tabular-nums"
    ].join(";");

    input.addEventListener("input", () => {
      output.value = Math.round(Number(input.value)).toString();
      output.textContent = output.value;
    });

    group.appendChild(label);
    group.appendChild(input);
    group.appendChild(output);
    return { group, input, output };
  };

  const angle = makeRange("Angle", 5, 85, 1);
  const power = makeRange("Puissance", 50, 400, 5);

  const move = document.createElement("button");
  move.type = "button";
  move.textContent = "BOUGER";
  move.setAttribute("aria-label", "Changer de toit, utilisable une fois");
  move.style.cssText = [
    "flex:0 0 auto",
    "height:48px",
    "min-width:88px",
    "box-sizing:border-box",
    "border:0",
    "border-radius:10px",
    "padding:0 12px",
    "font:850 14px system-ui,-apple-system,BlinkMacSystemFont,sans-serif",
    "letter-spacing:.025em",
    "color:#eafaff",
    "background:linear-gradient(#399dcc,#176188)",
    "box-shadow:0 4px 0 #0b3654",
    "cursor:pointer",
    "touch-action:manipulation"
  ].join(";");

  const fire = document.createElement("button");
  fire.type = "button";
  fire.textContent = "TIRER";
  fire.setAttribute("aria-label", "Tirer la banane");
  fire.style.cssText = [
    "flex:0 0 auto",
    "height:48px",
    "min-width:102px",
    "box-sizing:border-box",
    "border:0",
    "border-radius:10px",
    "padding:0 18px",
    "font:900 17px system-ui,-apple-system,BlinkMacSystemFont,sans-serif",
    "letter-spacing:.04em",
    "color:#071326",
    "background:linear-gradient(#ffe177,#ffb82d)",
    "box-shadow:0 4px 0 #b66f00",
    "cursor:pointer",
    "touch-action:manipulation"
  ].join(";");

  panel.appendChild(angle.group);
  panel.appendChild(power.group);
  panel.appendChild(move);
  panel.appendChild(fire);
  document.body.appendChild(panel);

  const stopForGame = (event) => event.stopPropagation();
  [
    "keydown", "keyup", "keypress", "beforeinput", "input",
    "pointerdown", "pointermove", "pointerup",
    "mousedown", "mouseup", "touchstart", "touchmove", "touchend"
  ].forEach((name) => panel.addEventListener(name, stopForGame));

  panel.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      state.cancelled = true;
    } else if (event.key === "Enter" && event.target !== fire) {
      event.preventDefault();
      state.fired = true;
    }
  }, true);

  fire.addEventListener("click", (event) => {
    event.preventDefault();
    state.fired = true;
    fire.blur();
  });

  move.addEventListener("click", (event) => {
    event.preventDefault();
    if (!move.disabled) {
      state.moveRequested = true;
    }
    move.blur();
  });

  const setMoveAvailable = (available) => {
    move.disabled = !available;
    move.textContent = available ? "BOUGER" : "FAIT";
    move.style.opacity = available ? "1" : ".48";
    move.style.cursor = available ? "pointer" : "default";
    move.style.boxShadow = available ? "0 4px 0 #0b3654" : "none";
  };

  const setRange = (control, value) => {
    control.input.value = String(value);
    control.output.value = Math.round(Number(control.input.value)).toString();
    control.output.textContent = control.output.value;
  };

  const applyLayout = () => {
    const portrait = window.innerHeight > window.innerWidth;
    const compact = !portrait && (
      (window.visualViewport ? window.visualViewport.height : window.innerHeight) <= 430
      || (window.visualViewport ? window.visualViewport.width : window.innerWidth) <= 700
    );
    panel.style.flexWrap = portrait ? "wrap" : "nowrap";
    panel.style.gap = compact ? "5px" : (portrait ? "6px 10px" : "12px");
    panel.style.padding = compact ? "6px" : (portrait ? "7px 9px" : "10px 12px");
    fire.style.height = compact || portrait ? "42px" : "48px";
    fire.style.minWidth = compact ? "78px" : (portrait ? "96px" : "102px");
    move.style.height = compact || portrait ? "42px" : "48px";
    move.style.minWidth = compact ? "72px" : (portrait ? "82px" : "88px");
    move.style.padding = compact ? "0 7px" : "0 12px";
    move.style.fontSize = compact ? "12px" : "14px";
  };
  window.addEventListener("resize", applyLayout);
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", applyLayout, { passive: true });
  }

  window.GorillaAimControls = {
    show(angleValue, powerValue, canMove) {
      state.fired = false;
      state.moveRequested = false;
      state.cancelled = false;
      setRange(angle, angleValue);
      setRange(power, powerValue);
      setMoveAvailable(Boolean(canMove));
      applyLayout();
      panel.style.display = "flex";
      document.body.classList.add("aiming");
      window.GorillaMobileShell?.scheduleViewportSync();
    },
    hide() {
      panel.style.display = "none";
      document.body.classList.remove("aiming");
      window.GorillaMobileShell?.scheduleViewportSync();
      state.fired = false;
      state.moveRequested = false;
      state.cancelled = false;
    },
    setValues(angleValue, powerValue) {
      setRange(angle, angleValue);
      setRange(power, powerValue);
    },
    values() {
      return {
        angle: Number(angle.input.value),
        power: Number(power.input.value)
      };
    },
    fired() {
      const value = state.fired;
      state.fired = false;
      return value;
    },
    moveRequested() {
      const value = state.moveRequested;
      state.moveRequested = false;
      return value;
    },
    cancelled() {
      const value = state.cancelled;
      state.cancelled = false;
      return value;
    }
  };

  return true;
})()
"""
        return bool(self._eval(code))

    def show(self, angle=45.0, power=180.0, can_move=False):
        if self.available:
            self._eval(
                "window.GorillaAimControls.show(%s, %s, %s)"
                % (
                    json.dumps(float(angle)),
                    json.dumps(float(power)),
                    json.dumps(bool(can_move)),
                )
            )

    def hide(self):
        if self.available:
            self._eval("window.GorillaAimControls.hide()")

    def set_values(self, angle, power):
        if self.available:
            self._eval(
                "window.GorillaAimControls.setValues(%s, %s)"
                % (json.dumps(float(angle)), json.dumps(float(power)))
            )

    def values(self):
        if not self.available:
            return None
        raw = self._eval("JSON.stringify(window.GorillaAimControls.values())")
        try:
            values = json.loads(str(raw))
            return float(values["angle"]), float(values["power"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def fired(self):
        return bool(self.available and self._eval("window.GorillaAimControls.fired()"))

    def move_requested(self):
        return bool(
            self.available
            and self._eval("window.GorillaAimControls.moveRequested()")
        )

    def cancelled(self):
        return bool(self.available and self._eval("window.GorillaAimControls.cancelled()"))


def clean_number_text(text):
    cleaned = []
    for ch in (text or "").replace(",", "."):
        if ch.isdigit() or ch in ".-":
            cleaned.append(ch)
    return "".join(cleaned)


def parse_number(text):
    try:
        return float((text or "").replace(",", "."))
    except ValueError:
        return None
