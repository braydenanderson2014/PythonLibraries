const state = {
  config: null,
  devices: [],
  selectedRuleIndex: 0,
  dashboardMode: false,
  autoPreviewTimeoutId: null,
  clockIntervalId: null,
  autoSaveInFlight: false,
  autoSaveQueued: false,
  nextTriggerAt: null,
  nextTriggerMessage: "Run a status refresh to calculate the next trigger.",
  triggerForecasts: [],
  nextPreviewAt: null,
  autoRefreshEnabled: false,
  autoRefreshInFlight: false,
  autoRefreshMessage: "Automatic status refresh is idle.",
  activeWatering: [],
};

const elements = {};

document.addEventListener("DOMContentLoaded", async () => {
  cacheElements();
  bindEvents();
  startClock();
  await loadConfig({ runImmediateAutomation: true });
});

function cacheElements() {
  elements.heroTitle = document.getElementById("hero-title");
  elements.heroCopy = document.getElementById("hero-copy");
  elements.configPath = document.getElementById("config-path");
  elements.configValidation = document.getElementById("config-validation");
  elements.settingsPanel = document.getElementById("settings-panel");
  elements.rulesPanel = document.getElementById("rules-panel");
  elements.settingsOverlay = document.getElementById("settings-overlay");
  elements.openSettings = document.getElementById("open-settings");
  elements.closeSettings = document.getElementById("close-settings");
  elements.saveStatus = document.getElementById("save-status");
  elements.locationQuery = document.getElementById("location-query");
  elements.locationStatus = document.getElementById("location-status");
  elements.locationResults = document.getElementById("location-results");
  elements.setupEyebrow = document.getElementById("setup-eyebrow");
  elements.setupTitle = document.getElementById("setup-title");
  elements.rulesList = document.getElementById("rules-list");
  elements.rulesEyebrow = document.getElementById("rules-eyebrow");
  elements.rulesTitle = document.getElementById("rules-title");
  elements.rulesCopy = document.getElementById("rules-copy");
  elements.programsNote = document.getElementById("programs-note");
  elements.devicesList = document.getElementById("devices-list");
  elements.devicesStatus = document.getElementById("devices-status");
  elements.previewStatus = document.getElementById("preview-status");
  elements.temperatureSummary = document.getElementById("temperature-summary");
  elements.forecastSummary = document.getElementById("forecast-summary");
  elements.forecastList = document.getElementById("forecast-list");
  elements.activeWateringList = document.getElementById("active-watering-list");
  elements.decisionsList = document.getElementById("decisions-list");
  elements.historyList = document.getElementById("history-list");
  elements.currentTime = document.getElementById("current-time");
  elements.nextTrigger = document.getElementById("next-trigger");
  elements.nextTriggerDetail = document.getElementById("next-trigger-detail");
  elements.delayStatus = document.getElementById("delay-status");
  elements.delayStatusDetail = document.getElementById("delay-status-detail");
  elements.forecastRisk = document.getElementById("forecast-risk");
  elements.forecastRiskDetail = document.getElementById("forecast-risk-detail");
  elements.manualDelayHours = document.getElementById("manual-delay-hours");
  elements.applyWeatherDelay = document.getElementById("apply-weather-delay");
  elements.clearWeatherDelay = document.getElementById("clear-weather-delay");
  elements.manualStatus = document.getElementById("manual-status");
  elements.manualDevice = document.getElementById("manual-device");
  elements.manualStation = document.getElementById("manual-station");
  elements.manualMinutes = document.getElementById("manual-minutes");

  elements.bhyveEmail = document.getElementById("bhyve-email");
  elements.credentialMode = document.getElementById("credential-mode");
  elements.bhyvePasswordEnv = document.getElementById("bhyve-password-env");
  elements.bhyvePassword = document.getElementById("bhyve-password");
  elements.bhyveApiKey = document.getElementById("bhyve-api-key");
  elements.clearSavedPassword = document.getElementById("clear-saved-password");
  elements.passwordHint = document.getElementById("password-hint");
  elements.apiKeyHint = document.getElementById("api-key-hint");

  elements.weatherLatitude = document.getElementById("weather-latitude");
  elements.weatherLongitude = document.getElementById("weather-longitude");
  elements.weatherUnit = document.getElementById("weather-unit");

  elements.pollInterval = document.getElementById("poll-interval");
  elements.requestTimeout = document.getElementById("request-timeout");
  elements.scheduleGuard = document.getElementById("schedule-guard");
  elements.stateFile = document.getElementById("state-file");
  elements.defaultCooldown = document.getElementById("default-cooldown");
  elements.defaultMaxRuns = document.getElementById("default-max-runs");
  elements.autoWeatherDelayEnabled = document.getElementById("auto-weather-delay-enabled");
  elements.autoWeatherDelayThreshold = document.getElementById("auto-weather-delay-threshold");
  elements.autoWeatherDelayHours = document.getElementById("auto-weather-delay-hours");
}

function bindEvents() {
  document.getElementById("save-config").addEventListener("click", saveConfig);
  document.getElementById("lookup-location").addEventListener("click", lookupLocation);
  document.getElementById("add-rule").addEventListener("click", addRule);
  document.getElementById("load-devices").addEventListener("click", loadDevices);
  document.getElementById("preview-decisions").addEventListener("click", previewDecisions);
  elements.applyWeatherDelay.addEventListener("click", applyManualWeatherDelay);
  elements.clearWeatherDelay.addEventListener("click", clearManualWeatherDelay);
  document.getElementById("start-manual").addEventListener("click", startManualWatering);
  document.getElementById("stop-manual").addEventListener("click", stopManualWatering);
  elements.manualDevice.addEventListener("change", syncManualStations);
  elements.credentialMode.addEventListener("change", syncCredentialFields);
  elements.openSettings.addEventListener("click", openSettingsDrawer);
  elements.closeSettings.addEventListener("click", closeSettingsDrawer);
  elements.settingsOverlay.addEventListener("click", closeSettingsDrawer);
  document.querySelectorAll("[data-scroll-target]").forEach((button) => {
    button.addEventListener("click", () => {
      scrollToPanel(button.dataset.scrollTarget);
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeSettingsDrawer();
    }
  });
  elements.locationQuery.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      lookupLocation();
    }
  });

  // Persist config edits when a field loses focus or a selection changes.
  elements.settingsPanel.addEventListener("change", handleConfigFieldChange);
  elements.rulesPanel.addEventListener("change", handleConfigFieldChange);
}

function openSettingsDrawer() {
  if (!state.dashboardMode) {
    return;
  }
  document.body.classList.add("settings-open");
}

function closeSettingsDrawer() {
  document.body.classList.remove("settings-open");
}

function scrollToPanel(panelId) {
  if (panelId === "settings-panel") {
    openSettingsDrawer();
    return;
  }

  closeSettingsDrawer();
  const target = document.getElementById(panelId);
  if (!target) {
    return;
  }
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

function applyInterfaceMode(meta) {
  state.dashboardMode = !Boolean(meta?.is_default_template);
  document.body.classList.toggle("dashboard-mode", state.dashboardMode);
  document.body.classList.toggle("setup-mode", !state.dashboardMode);
  if (!state.dashboardMode) {
    closeSettingsDrawer();
  }
  updateInterfaceCopy();
}

function updateInterfaceCopy() {
  if (state.dashboardMode) {
    elements.heroTitle.textContent = "Operations Dashboard";
    elements.heroCopy.textContent = "Keep status front and center, review forecast risk and delay state, run manual watering, and keep the underlying controller settings tucked inside the settings drawer until you need them.";
    elements.setupEyebrow.textContent = "Settings";
    elements.setupTitle.textContent = "Controller Settings";
    document.getElementById("save-config").textContent = "Save Settings";
    elements.rulesEyebrow.textContent = "Programs";
    elements.rulesTitle.textContent = "Automation Programs";
    elements.rulesCopy.textContent = "Create controller-owned automation programs, adjust their thresholds and time windows, and turn them on or off without touching your native Orbit schedules.";
    document.getElementById("add-rule").textContent = "New Program";
    document.getElementById("preview-decisions").textContent = "Refresh Status";
    document.getElementById("load-devices").textContent = "Refresh Devices";
  } else {
    elements.heroTitle.textContent = "Control Room";
    elements.heroCopy.textContent = "Configure the controller, discover device and zone IDs, review status and forecast decisions, and run manual watering without editing JSON by hand.";
    elements.setupEyebrow.textContent = "Setup";
    elements.setupTitle.textContent = "Config Builder";
    document.getElementById("save-config").textContent = "Save Config";
    elements.rulesEyebrow.textContent = "Rules";
    elements.rulesTitle.textContent = "Temperature Rules";
    elements.rulesCopy.textContent = "Pick a rule card, then use device discovery to stamp the matching device ID and station into that rule.";
    document.getElementById("add-rule").textContent = "Add Rule";
    document.getElementById("preview-decisions").textContent = "Refresh Status";
    document.getElementById("load-devices").textContent = "Load Devices";
  }
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json();
}

function getPollIntervalSeconds() {
  // UI display always refreshes quickly (reads the backend's cached result — no BHyve API calls).
  // The backend automation cycle runs at its own configured poll_interval_seconds.
  return 30;
}

function hasConfiguredAuth(payload) {
  const credentialMode = payload?.config?.bhyve?.credential_mode || payload?.meta?.credential_mode;
  const hasEmail = Boolean(payload?.config?.bhyve?.email?.trim());
  const hasSavedPassword = Boolean(payload?.meta?.has_saved_password);
  const hasSavedApiKey = Boolean(payload?.meta?.has_saved_api_key);

  if (credentialMode === "token") {
    return hasSavedApiKey;
  }
  if (credentialMode === "password") {
    return hasEmail && hasSavedPassword;
  }
  return hasEmail && Boolean(payload?.validation?.valid);
}

function canAutoPreview(payload) {
  return hasConfiguredAuth(payload) && Boolean(payload?.validation?.valid);
}

function clearAutoPreviewTimeout() {
  if (state.autoPreviewTimeoutId !== null) {
    clearTimeout(state.autoPreviewTimeoutId);
    state.autoPreviewTimeoutId = null;
  }
}

function setNextPreviewAt(date) {
  state.nextPreviewAt = date instanceof Date ? date : null;
  renderClock();
}

function setNextRuleTrigger(trigger = null, fallbackMessage = "Run a status refresh to calculate the next trigger.", forecasts = []) {
  state.triggerForecasts = (forecasts || []).filter((f) => f.at != null);
  if (trigger?.at) {
    const parsedDate = new Date(trigger.at);
    state.nextTriggerAt = Number.isNaN(parsedDate.getTime()) ? null : parsedDate;
  } else {
    state.nextTriggerAt = state.triggerForecasts.length > 0 ? new Date(state.triggerForecasts[0].at) : null;
  }
  state.nextTriggerMessage = trigger?.detail || fallbackMessage;
  renderClock();
}

function startClock() {
  if (state.clockIntervalId !== null) {
    clearInterval(state.clockIntervalId);
  }
  renderClock();
  state.clockIntervalId = setInterval(renderClock, 1000);
}

function renderClock() {
  const now = new Date();
  elements.currentTime.textContent = now.toLocaleString();
  updateActiveWateringCountdowns(now);
  updateDecisionCooldownCountdowns(now);

  // Render all upcoming triggers as a list.
  if (!state.triggerForecasts.length) {
    elements.nextTrigger.innerHTML = "<span class='trigger-forecast-empty'>Not scheduled</span>";
  } else {
    elements.nextTrigger.innerHTML = state.triggerForecasts
      .map((f) => {
        if (!f.at) {
          // Blocked rule — no predictable trigger time.
          return `<div class="trigger-forecast-item trigger-forecast-waiting"><span class="trigger-forecast-name">${escapeHtml(f.rule_name || "")}:</span><span class="trigger-forecast-time">${escapeHtml(f.detail || "Waiting")}</span></div>`;
        }
        const d = new Date(f.at);
        const isToday = d.toDateString() === now.toDateString();
        const isTomorrow =
          d.toDateString() === new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1).toDateString();
        const timeStr = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        const dayLabel = isToday ? "Today" : isTomorrow ? "Tomorrow" : d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
        const remaining = d.getTime() - now.getTime();
        let countdownStr = "";
        if (remaining > 0 && remaining < 24 * 60 * 60 * 1000) {
          const totalSeconds = Math.ceil(remaining / 1000);
          const h = Math.floor(totalSeconds / 3600);
          const m = Math.floor((totalSeconds % 3600) / 60);
          const s = totalSeconds % 60;
          countdownStr = h > 0 ? ` (in ${h}h ${m}m)` : m > 0 ? ` (in ${m}m ${s}s)` : ` (in ${s}s)`;
        }
        return `<div class="trigger-forecast-item"><span class="trigger-forecast-name">${escapeHtml(f.rule_name || "")}:</span><span class="trigger-forecast-time">${dayLabel} at ${timeStr}${countdownStr}</span></div>`;
      })
      .join("");
  }

  let previewRefreshDetail = "";
  if (state.autoRefreshEnabled) {
    previewRefreshDetail = state.autoRefreshMessage;
    if (state.nextPreviewAt) {
      const millisecondsRemaining = state.nextPreviewAt.getTime() - now.getTime();
      if (millisecondsRemaining <= 0) {
        previewRefreshDetail = "Refreshing status now...";
      } else {
        const totalSeconds = Math.ceil(millisecondsRemaining / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        previewRefreshDetail = `Next automatic status refresh in ${minutes}:${String(seconds).padStart(2, "0")}.`;
      }
    }
  }

  elements.nextTriggerDetail.textContent = [state.nextTriggerMessage, previewRefreshDetail]
    .filter(Boolean)
    .join(" ");
}

function scheduleNextAutoPreview(delaySeconds = getPollIntervalSeconds()) {
  if (!state.autoRefreshEnabled) {
    setNextPreviewAt(null);
    return;
  }
  clearAutoPreviewTimeout();
  const delayMilliseconds = Math.max(1000, Number(delaySeconds) * 1000);
  setNextPreviewAt(new Date(Date.now() + delayMilliseconds));
  state.autoPreviewTimeoutId = setTimeout(async () => {
    await runAutomaticRefresh();
  }, delayMilliseconds);
}

async function runAutomaticRefresh() {
  if (!state.autoRefreshEnabled || state.autoRefreshInFlight) {
    return;
  }

  state.autoRefreshInFlight = true;
  try {
    await previewDecisions({ saveConfigFirst: false, automatic: true });
  } finally {
    state.autoRefreshInFlight = false;
    if (state.autoRefreshEnabled) {
      scheduleNextAutoPreview();
    }
  }
}

async function applyConfigPayload(payload, { runImmediateAutomation = false } = {}) {
  clearAutoPreviewTimeout();
  setNextPreviewAt(null);
  state.config = payload.config;
  applyInterfaceMode(payload.meta);
  renderConfig(payload);
  const canLoadDevicesAutomatically = hasConfiguredAuth(payload);
  state.autoRefreshEnabled = canAutoPreview(payload);
  state.autoRefreshMessage = state.autoRefreshEnabled
    ? "Waiting for the next automatic status refresh window."
    : canLoadDevicesAutomatically
      ? "Automatic status refresh waits for a valid saved config."
      : "Automatic status refresh is idle.";

  setNextRuleTrigger(null, state.autoRefreshEnabled ? "Calculating the next trigger from the latest status refresh..." : state.autoRefreshMessage);

  if (!state.autoRefreshEnabled) {
    clearAutoPreviewTimeout();
  }

  if (runImmediateAutomation) {
    if (canLoadDevicesAutomatically) {
      await loadDevices({ saveConfigFirst: false, automatic: true });
    }
    if (state.autoRefreshEnabled) {
      await previewDecisions({ saveConfigFirst: false, automatic: true });
    }
  }

  if (state.autoRefreshEnabled) {
    scheduleNextAutoPreview();
  }
  renderClock();
}

async function loadConfig({ runImmediateAutomation = false } = {}) {
  try {
    const payload = await apiRequest("/api/config");
    await applyConfigPayload(payload, { runImmediateAutomation });
    setBanner(elements.saveStatus, payload.validation.valid ? "Config loaded." : payload.validation.error, payload.validation.valid ? "success" : "error");
  } catch (error) {
    setBanner(elements.saveStatus, error.message, "error");
  }
}

function renderConfig(payload) {
  const { config, meta, validation } = payload;
  state.config = config;
  if (state.selectedRuleIndex >= config.rules.length) {
    state.selectedRuleIndex = Math.max(0, config.rules.length - 1);
  }

  elements.configPath.textContent = meta.config_path;
  elements.configValidation.textContent = validation.valid ? `Valid • ${validation.rule_count} rules` : "Needs attention";
  elements.configValidation.className = `pill ${validation.valid ? "valid" : "invalid"}`;

  fillTopLevelFields(config);
  syncCredentialFields(meta);
  renderRules();
  renderManualDeviceOptions();
}

function fillTopLevelFields(config) {
  const bhyve = config.bhyve || {};
  const weather = config.weather || {};
  const controller = config.controller || {};

  elements.bhyveEmail.value = bhyve.email || "";
  elements.credentialMode.value = bhyve.credential_mode || "env";
  elements.bhyvePasswordEnv.value = bhyve.password_env || "";
  elements.bhyvePassword.value = "";
  elements.bhyveApiKey.value = "";
  elements.clearSavedPassword.checked = false;

  elements.weatherLatitude.value = weather.latitude ?? "";
  elements.weatherLongitude.value = weather.longitude ?? "";
  elements.weatherUnit.value = weather.temperature_unit || "fahrenheit";

  elements.pollInterval.value = bhyve.poll_interval_seconds ?? 300;
  elements.requestTimeout.value = bhyve.request_timeout_seconds ?? 30;
  elements.scheduleGuard.value = controller.schedule_guard_minutes ?? 30;
  elements.stateFile.value = controller.state_file || ".bhyve_state.json";
  elements.defaultCooldown.value = controller.default_cooldown_minutes ?? 120;
  elements.defaultMaxRuns.value = controller.default_max_runs_per_day ?? 3;
  elements.autoWeatherDelayEnabled.checked = Boolean(controller.automatic_weather_delay_enabled);
  elements.autoWeatherDelayThreshold.value = controller.automatic_weather_delay_probability_threshold ?? 60;
  elements.autoWeatherDelayHours.value = controller.automatic_weather_delay_lookahead_hours ?? 12;
}

function syncCredentialFields(meta = null) {
  const credentialMode = elements.credentialMode.value;
  const usingEnv = credentialMode === "env";
  const usingPassword = credentialMode === "password";
  const usingToken = credentialMode === "token";
  const hasSavedPassword = Boolean(meta?.has_saved_password);
  const hasSavedApiKey = Boolean(meta?.has_saved_api_key);
  const legacyPasswordInEnv = Boolean(meta?.legacy_password_in_env);

  elements.bhyvePasswordEnv.disabled = !usingEnv;
  elements.bhyvePassword.disabled = !usingPassword;
  elements.bhyveApiKey.disabled = !usingToken;
  elements.clearSavedPassword.disabled = !usingPassword;

  elements.bhyvePasswordEnv.closest(".field").hidden = !usingEnv;
  elements.bhyvePassword.closest(".field").hidden = !usingPassword;
  elements.bhyveApiKey.closest(".field").hidden = !usingToken;
  elements.clearSavedPassword.closest(".field").hidden = !usingPassword;

  if (usingPassword) {
    if (legacyPasswordInEnv) {
      elements.passwordHint.textContent = "This config currently has a saved password in the wrong field. Save once and the UI will move it to the proper password field.";
    } else if (hasSavedPassword) {
      elements.passwordHint.textContent = "A password is already stored. Leave the field blank to keep it, or check the box to remove it.";
    } else {
      elements.passwordHint.textContent = "Enter the real BHyve password here if you want it stored in config.json.";
    }
  } else if (usingToken) {
    elements.apiKeyHint.textContent = hasSavedApiKey
      ? "An Orbit API token is already stored. Leave this blank to keep it, or paste a new token to replace it."
      : "Paste the orbit_api_key from an authenticated Orbit dashboard session. This is the practical option for Google-backed BHyve accounts.";
  } else {
    elements.passwordHint.textContent = "Use the name of an environment variable, such as BHYVE_PASSWORD. The app will read the password from your system environment.";
  }
}

function renderRules() {
  const rules = state.config?.rules || [];
  const itemLabel = state.dashboardMode ? "Program" : "Rule";
  if (!rules.length) {
    elements.rulesList.innerHTML = `<div class="empty-state">No ${itemLabel.toLowerCase()}s yet. Add one to start driving watering.</div>`;
    return;
  }

  const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  elements.rulesList.innerHTML = rules
    .map((rule, index) => {
      const selected = index === state.selectedRuleIndex;
      const ruleType = rule.type || "temperature";
      const isSchedule = ruleType === "schedule";
      const [startHour, endHour] = Array.isArray(rule.allowed_hours_local)
        ? rule.allowed_hours_local
        : ["", ""];
      const [cooldownMin, cooldownMax] = Array.isArray(rule.cooldown_minutes_range)
        ? rule.cooldown_minutes_range
        : ["", ""];

      // Schedule-specific: times and days.
      const scheduleTimesStr = (rule.schedule_times || [])
        .map((t) => {
          const h = typeof t === "object" ? t.hour : 0;
          const m = typeof t === "object" ? t.minute : 0;
          return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
        })
        .join(", ");
      const activeDays = new Set(Array.isArray(rule.schedule_days) ? rule.schedule_days : []);
      const dayCheckboxes = DAY_NAMES.map((day, i) =>
        `<label class="day-checkbox">
          <input type="checkbox" data-field="schedule_day" data-day-index="${i}" data-rule-index="${index}" ${activeDays.has(i) ? "checked" : ""} />
          <span>${day}</span>
        </label>`
      ).join("");

      return `
        <article class="rule-card ${selected ? "selected" : ""}" data-rule-index="${index}">
          <div class="rule-card-header">
            <div>
              <div class="rule-card-title">${escapeHtml(rule.name || `${itemLabel} ${index + 1}`)}</div>
              <div class="device-meta mono">Device ${escapeHtml(rule.device_id || "not set")} • Station ${escapeHtml(String(rule.station ?? ""))}</div>
            </div>
            <div class="rule-card-actions">
              <button class="button" type="button" data-select-rule="${index}">Select</button>
              <button class="button" type="button" data-remove-rule="${index}">Remove</button>
            </div>
          </div>
          <div class="rule-grid">
            <label class="full">
              <span>Rule name</span>
              <input type="text" data-field="name" data-rule-index="${index}" value="${escapeAttribute(rule.name || "")}" />
            </label>
            <label>
              <span>Device ID</span>
              <input type="text" class="mono" data-field="device_id" data-rule-index="${index}" value="${escapeAttribute(rule.device_id || "")}" />
            </label>
            <label>
              <span>Station</span>
              <input type="number" min="1" data-field="station" data-rule-index="${index}" value="${escapeAttribute(rule.station ?? 1)}" />
            </label>
            <label>
              <span>Rule type</span>
              <select data-field="rule_type" data-rule-index="${index}">
                <option value="temperature" ${!isSchedule ? "selected" : ""}>Temperature trigger</option>
                <option value="schedule" ${isSchedule ? "selected" : ""}>Scheduled time</option>
              </select>
            </label>
            <label>
              <span>Run minutes</span>
              <input type="number" min="0.1" step="0.1" data-field="manual_run_minutes" data-rule-index="${index}" value="${escapeAttribute(rule.manual_run_minutes ?? 10)}" />
            </label>

            ${isSchedule ? `
            <div class="field full schedule-times-field">
              <span>Run times <small>(comma-separated HH:MM, e.g. 06:00, 18:00)</small></span>
              <input type="text" data-field="schedule_times_str" data-rule-index="${index}" value="${escapeAttribute(scheduleTimesStr)}" placeholder="06:00" />
            </div>
            <div class="field full">
              <span>Run days <small>(leave all unchecked to run every day)</small></span>
              <div class="day-picker">${dayCheckboxes}</div>
            </div>
            <label>
              <span>Min temperature (skip below)</span>
              <input type="number" step="0.1" data-field="min_temperature" data-rule-index="${index}" value="${escapeAttribute(rule.min_temperature ?? "")}" placeholder="optional" />
            </label>
            ` : `
            <label>
              <span>Start above</span>
              <input type="number" step="0.1" data-field="start_above" data-rule-index="${index}" value="${escapeAttribute(rule.start_above ?? 88)}" />
            </label>
            <label>
              <span>Stop below</span>
              <input type="number" step="0.1" data-field="stop_below" data-rule-index="${index}" value="${escapeAttribute(rule.stop_below ?? 78)}" />
            </label>
            <label>
              <span>Allowed hour start</span>
              <input type="number" min="0" max="23" data-field="allowed_hours_start" data-rule-index="${index}" value="${escapeAttribute(startHour)}" />
            </label>
            <label>
              <span>Allowed hour end</span>
              <input type="number" min="0" max="23" data-field="allowed_hours_end" data-rule-index="${index}" value="${escapeAttribute(endHour)}" />
            </label>
            <label>
              <span>Cooldown min</span>
              <input type="number" min="1" data-field="cooldown_minutes_min" data-rule-index="${index}" value="${escapeAttribute(cooldownMin)}" />
            </label>
            <label>
              <span>Cooldown max</span>
              <input type="number" min="1" data-field="cooldown_minutes_max" data-rule-index="${index}" value="${escapeAttribute(cooldownMax)}" />
            </label>
            `}

            <label>
              <span>Cooldown (minutes)</span>
              <input type="number" min="1" data-field="cooldown_minutes" data-rule-index="${index}" value="${escapeAttribute(rule.cooldown_minutes ?? "")}" />
            </label>
            <label>
              <span>Max runs per day</span>
              <input type="number" min="1" data-field="max_runs_per_day" data-rule-index="${index}" value="${escapeAttribute(rule.max_runs_per_day ?? "")}" />
            </label>
            <label class="checkbox-field full">
              <input type="checkbox" data-field="stop_external_watering" data-rule-index="${index}" ${rule.stop_external_watering ? "checked" : ""} />
              <span>Immediately stop watering that was not started by this program.</span>
            </label>
            <label class="checkbox-field full">
              <input type="checkbox" data-field="pause_on_motion" data-rule-index="${index}" ${rule.pause_on_motion ? "checked" : ""} />
              <span>Pause watering when motion is detected nearby.</span>
            </label>
            <label>
              <span>Motion pause minutes</span>
              <input type="number" min="1" data-field="motion_pause_minutes" data-rule-index="${index}" value="${escapeAttribute(rule.motion_pause_minutes ?? 15)}" />
            </label>
            <label class="checkbox-field full">
              <input type="checkbox" data-field="enabled" data-rule-index="${index}" ${rule.enabled !== false ? "checked" : ""} />
              <span>${state.dashboardMode ? "Program enabled" : "Rule enabled"}</span>
            </label>
          </div>
        </article>
      `;
    })
    .join("");

  elements.rulesList.querySelectorAll("[data-select-rule]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedRuleIndex = Number(button.dataset.selectRule);
      renderRules();
    });
  });

  elements.rulesList.querySelectorAll("[data-remove-rule]").forEach((button) => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.removeRule);
      collectConfigFromForm();
      state.config.rules.splice(index, 1);
      if (state.selectedRuleIndex >= state.config.rules.length) {
        state.selectedRuleIndex = Math.max(0, state.config.rules.length - 1);
      }
      renderRules();
    });
  });

  // Re-render when rule type changes so the correct fields appear.
  elements.rulesList.querySelectorAll("[data-field='rule_type']").forEach((select) => {
    select.addEventListener("change", () => {
      collectConfigFromForm();
      renderRules();
    });
  });
}

function collectConfigFromForm() {
  if (!state.config) {
    return null;
  }

  const rules = Array.from(elements.rulesList.querySelectorAll(".rule-card")).map((card) => {
    const find = (field) => card.querySelector(`[data-field="${field}"]`);
    const ruleTypeEl = find("rule_type");
    const ruleType = ruleTypeEl ? ruleTypeEl.value : "temperature";

    const base = {
      type: ruleType,
      name: find("name").value.trim(),
      device_id: find("device_id").value.trim(),
      station: Number(find("station").value || 1),
      manual_run_minutes: Number(find("manual_run_minutes").value || 1),
      cooldown_minutes: optionalNumber(find("cooldown_minutes")?.value),
      max_runs_per_day: optionalNumber(find("max_runs_per_day")?.value),
      stop_external_watering: find("stop_external_watering").checked,
      pause_on_motion: find("pause_on_motion").checked,
      motion_pause_minutes: optionalNumber(find("motion_pause_minutes")?.value),
      enabled: find("enabled").checked,
    };

    if (ruleType === "schedule") {
      // Parse comma-separated HH:MM times.
      const timesRaw = (find("schedule_times_str")?.value || "").trim();
      const scheduleTimes = timesRaw
        ? timesRaw.split(",").map((s) => {
            const [h, m] = s.trim().split(":").map(Number);
            return { hour: isNaN(h) ? 0 : h, minute: isNaN(m) ? 0 : m };
          })
        : [];
      // Collect checked day checkboxes.
      const scheduleDays = [];
      card.querySelectorAll("[data-field='schedule_day']:checked").forEach((cb) => {
        scheduleDays.push(Number(cb.dataset.dayIndex));
      });
      scheduleDays.sort((a, b) => a - b);
      const minTempEl = find("min_temperature");
      return {
        ...base,
        schedule_times: scheduleTimes,
        schedule_days: scheduleDays,
        min_temperature: optionalNumber(minTempEl?.value),
      };
    }

    // Temperature rule fields.
    const allowedStart = find("allowed_hours_start")?.value;
    const allowedEnd = find("allowed_hours_end")?.value;
    const cooldownMinEl = find("cooldown_minutes_min");
    const cooldownMaxEl = find("cooldown_minutes_max");
    const cooldownMin = optionalNumber(cooldownMinEl?.value);
    const cooldownMax = optionalNumber(cooldownMaxEl?.value);
    const allowedHours = allowedStart != null && allowedStart !== "" && allowedEnd != null && allowedEnd !== ""
      ? [Number(allowedStart), Number(allowedEnd)]
      : null;
    const cooldownRange = cooldownMin != null && cooldownMax != null ? [cooldownMin, cooldownMax] : null;
    return {
      ...base,
      start_above: Number(find("start_above")?.value || 0),
      stop_below: Number(find("stop_below")?.value || 0),
      allowed_hours_local: allowedHours,
      cooldown_minutes_range: cooldownRange,
    };
  });

  state.config = {
    bhyve: {
      email: elements.bhyveEmail.value.trim(),
      credential_mode: elements.credentialMode.value,
      password_env: elements.bhyvePasswordEnv.value.trim(),
      password: elements.bhyvePassword.value,
      api_key: elements.bhyveApiKey.value.trim(),
      clear_saved_password: elements.clearSavedPassword.checked,
      poll_interval_seconds: Number(elements.pollInterval.value || 300),
      request_timeout_seconds: Number(elements.requestTimeout.value || 30),
    },
    weather: {
      provider: "open_meteo",
      latitude: Number(elements.weatherLatitude.value || 0),
      longitude: Number(elements.weatherLongitude.value || 0),
      temperature_unit: elements.weatherUnit.value,
    },
    controller: {
      schedule_guard_minutes: Number(elements.scheduleGuard.value || 30),
      default_cooldown_minutes: Number(elements.defaultCooldown.value || 120),
      default_max_runs_per_day: Number(elements.defaultMaxRuns.value || 3),
      automatic_weather_delay_enabled: elements.autoWeatherDelayEnabled.checked,
      automatic_weather_delay_probability_threshold: Number(elements.autoWeatherDelayThreshold.value || 60),
      automatic_weather_delay_lookahead_hours: Number(elements.autoWeatherDelayHours.value || 12),
      manual_weather_delay_until: state.config?.controller?.manual_weather_delay_until || null,
      state_file: elements.stateFile.value.trim() || ".bhyve_state.json",
    },
    rules,
    devices: state.config?.devices || [],
  };
  return state.config;
}

async function persistConfig(config, { runImmediateAutomation = false } = {}) {
  const payload = await apiRequest("/api/config", {
    method: "POST",
    body: JSON.stringify({ config }),
  });
  await applyConfigPayload(payload, { runImmediateAutomation });
  return payload;
}

async function saveConfig({ runImmediateAutomation = true } = {}) {
  try {
    const config = collectConfigFromForm();
    const payload = await persistConfig(config, { runImmediateAutomation });
    setSaveFeedback(
      payload.validation.valid
        ? "Config saved successfully."
        : `Config saved, but validation still needs attention: ${payload.validation.error}`,
      payload.validation.valid ? "success" : "error",
    );
  } catch (error) {
    setSaveFeedback(error.message, "error");
  }
}

function setSaveFeedback(message, tone = "success") {
  setBanner(elements.saveStatus, message, tone);
  if (state.dashboardMode && elements.previewStatus) {
    setBanner(elements.previewStatus, message, tone);
  }
}

function handleConfigFieldChange(event) {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  if (target.closest("#location-query")) {
    return;
  }
  if (!isFieldReadyForAutoSave(target)) {
    setSaveFeedback("Finish both paired values before auto-save runs.", "muted");
    return;
  }
  requestAutoSave();
}

function isFieldReadyForAutoSave(target) {
  if (!(target instanceof HTMLInputElement || target instanceof HTMLSelectElement || target instanceof HTMLTextAreaElement)) {
    return true;
  }

  const field = target.dataset.field;
  if (!field) {
    return true;
  }

  const card = target.closest(".rule-card");
  if (!card) {
    return true;
  }

  if (field === "cooldown_minutes_min" || field === "cooldown_minutes_max") {
    const minField = card.querySelector('[data-field="cooldown_minutes_min"]');
    const maxField = card.querySelector('[data-field="cooldown_minutes_max"]');
    const minValue = minField instanceof HTMLInputElement ? minField.value.trim() : "";
    const maxValue = maxField instanceof HTMLInputElement ? maxField.value.trim() : "";
    return (minValue === "" && maxValue === "") || (minValue !== "" && maxValue !== "");
  }

  if (field === "allowed_hours_start" || field === "allowed_hours_end") {
    const startField = card.querySelector('[data-field="allowed_hours_start"]');
    const endField = card.querySelector('[data-field="allowed_hours_end"]');
    const startValue = startField instanceof HTMLInputElement ? startField.value.trim() : "";
    const endValue = endField instanceof HTMLInputElement ? endField.value.trim() : "";
    return (startValue === "" && endValue === "") || (startValue !== "" && endValue !== "");
  }

  return true;
}

function requestAutoSave() {
  if (state.autoSaveInFlight) {
    state.autoSaveQueued = true;
    return;
  }
  void runAutoSave();
}

async function runAutoSave() {
  if (state.autoSaveInFlight) {
    state.autoSaveQueued = true;
    return;
  }
  state.autoSaveInFlight = true;
  try {
    do {
      state.autoSaveQueued = false;
      const config = collectConfigFromForm();
      const payload = await persistConfig(config, { runImmediateAutomation: false });
      setSaveFeedback(
        payload.validation.valid
          ? "Changes saved automatically."
          : `Changes saved, but validation still needs attention: ${payload.validation.error}`,
        payload.validation.valid ? "success" : "error",
      );
    } while (state.autoSaveQueued);
  } catch (error) {
    setSaveFeedback(`Auto-save failed: ${error.message}`, "error");
  } finally {
    state.autoSaveInFlight = false;
  }
}

function addRule() {
  collectConfigFromForm();
  const n = state.config.rules.length + 1;
  if (state.dashboardMode) {
    state.config.rules.push({
      type: "schedule",
      name: `Program ${n}`,
      device_id: "",
      station: 1,
      manual_run_minutes: 10,
      schedule_times: [{ hour: 6, minute: 0 }],
      schedule_days: [],
      min_temperature: null,
      cooldown_minutes: null,
      max_runs_per_day: null,
      stop_external_watering: false,
      pause_on_motion: false,
      motion_pause_minutes: 15,
      enabled: true,
    });
  } else {
    state.config.rules.push({
      type: "temperature",
      name: `Rule ${n}`,
      device_id: "",
      station: 1,
      start_above: 88,
      stop_below: 78,
      manual_run_minutes: 10,
      cooldown_minutes: null,
      cooldown_minutes_range: null,
      max_runs_per_day: null,
      allowed_hours_local: [10, 19],
      stop_external_watering: false,
      pause_on_motion: false,
      motion_pause_minutes: 15,
      enabled: true,
    });
  }
  state.selectedRuleIndex = state.config.rules.length - 1;
  renderRules();
}

async function loadDevices({ saveConfigFirst = true, automatic = false } = {}) {
  try {
    if (saveConfigFirst) {
      await saveConfig({ runImmediateAutomation: false });
    }
    const payload = await apiRequest("/api/devices");
    state.devices = payload.devices;
    renderDevices();
    renderManualDeviceOptions();
    setBanner(
      elements.devicesStatus,
      automatic ? `Loaded ${state.devices.length} device(s) automatically.` : `Loaded ${state.devices.length} device(s).`,
      "success"
    );
  } catch (error) {
    setBanner(elements.devicesStatus, error.message, "error");
  }
}

function renderDevices() {
  if (!state.devices.length) {
    elements.devicesList.innerHTML = `<div class="empty-state">No devices returned from Orbit BHyve.</div>`;
    return;
  }

  elements.devicesList.innerHTML = state.devices
    .map((device) => {
      const zones = (device.zones || [])
        .map(
          (zone) => `
            <div class="zone-chip">
              <div>
                <div><strong>${escapeHtml(zone.name)}</strong></div>
                <div class="zone-meta mono">station=${escapeHtml(String(zone.station))}</div>
              </div>
              <button class="button" type="button" data-device-id="${escapeAttribute(device.id)}" data-station="${escapeAttribute(zone.station)}">Use in selected rule</button>
            </div>
          `
        )
        .join("");

      const isBlocked = (state.config?.devices || [])
        .some((d) => d.device_id === device.id && d.block_unlisted_stations);

      return `
        <article class="device-card">
          <div class="device-card-header">
            <div class="device-name">${escapeHtml(device.name)}</div>
            <span class="pill ${device.is_connected ? "valid" : "invalid"}">${device.is_connected ? "Connected" : "Offline"}</span>
          </div>
          <div class="device-meta mono">id=${escapeHtml(device.id)} • type=${escapeHtml(device.type)}</div>
          <div class="device-meta">Next start: ${escapeHtml(device.next_start_time || "not scheduled")}</div>
          <div class="device-meta">Watering: ${escapeHtml(JSON.stringify(device.watering_status || null))}</div>
          <label class="device-restriction checkbox-field">
            <input type="checkbox" class="device-block-toggle" data-device-id="${escapeAttribute(device.id)}"${isBlocked ? " checked" : ""} />
            <span>Block unlisted stations</span>
          </label>
          <small class="device-restriction-hint">When on, any station the BHyve timer starts that has no rule here is stopped automatically.</small>
          <div class="zones-list">${zones || `<div class="zone-meta">No zones reported for this device.</div>`}</div>
        </article>
      `;
    })
    .join("");

  elements.devicesList.querySelectorAll("[data-device-id][data-station]").forEach((button) => {
    button.addEventListener("click", () => {
      applyDiscoveredZone(button.dataset.deviceId, Number(button.dataset.station));
    });
  });

  elements.devicesList.querySelectorAll(".device-block-toggle").forEach((toggle) => {
    toggle.addEventListener("change", () => {
      const deviceId = toggle.dataset.deviceId;
      const blocked = toggle.checked;
      const devices = (state.config?.devices || []).filter((d) => d.device_id !== deviceId);
      if (blocked) {
        devices.push({ device_id: deviceId, block_unlisted_stations: true });
      }
      if (!state.config) state.config = {};
      state.config.devices = devices;
      requestAutoSave();
    });
  });
}

async function applyDiscoveredZone(deviceId, station) {
  collectConfigFromForm();
  if (!state.config.rules.length) {
    addRule();
  }
  const rule = state.config.rules[state.selectedRuleIndex];
  rule.device_id = deviceId;
  rule.station = station;
  renderRules();
  try {
    await persistConfig(state.config, { runImmediateAutomation: false });
    setBanner(
      elements.devicesStatus,
      `Applied device ${deviceId} station ${station} to ${rule.name || `Rule ${state.selectedRuleIndex + 1}`} and saved the config.`,
      "success",
    );
  } catch (error) {
    setBanner(
      elements.devicesStatus,
      `Applied device ${deviceId} station ${station} locally, but saving failed: ${error.message}`,
      "error",
    );
  }
}

async function previewDecisions({ saveConfigFirst = true, automatic = false } = {}) {
  try {
    if (saveConfigFirst) {
      await saveConfig({ runImmediateAutomation: false });
    }
    const payload = await apiRequest("/api/status");
    renderPreview(payload);
    const automationDetail = describeAutomationStatus(payload.automation_status || null);
    setBanner(
      elements.previewStatus,
      automatic
        ? `Status refreshed automatically. ${automationDetail}`
        : `Status refreshed. ${automationDetail}`,
      "success"
    );
    if (!automatic && state.autoRefreshEnabled) {
      scheduleNextAutoPreview();
    }
  } catch (error) {
    setBanner(elements.previewStatus, error.message, "error");
  }
}

function renderPreview(payload) {
  setNextRuleTrigger(payload.next_trigger, "Run a status refresh to calculate the next trigger.", payload.trigger_forecasts);

  const forecast = payload.forecast || { entries: [], max_precipitation_probability: 0, total_precipitation: 0, lookahead_hours: 0 };
  const delayStatus = payload.delay_status || { active: false, manual_active: false, automatic_active: false, detail: "No weather delay is active." };
  state.activeWatering = payload.active_watering || [];
  renderActiveWatering();

  const observedAt = new Date(payload.temperature.observed_at).toLocaleString();
  elements.temperatureSummary.innerHTML = `
    <div class="temperature-value">${Number(payload.temperature.value).toFixed(1)} ${escapeHtml(payload.temperature.unit)}</div>
    <div>Observed at ${escapeHtml(observedAt)}</div>
  `;

  elements.delayStatus.textContent = describeDelayStatus(delayStatus);
  elements.delayStatusDetail.textContent = delayStatus.detail || "No weather delay is active.";
  elements.forecastRisk.textContent = `${Math.round(Number(forecast.max_precipitation_probability || 0))}%`;
  elements.forecastRiskDetail.textContent = `Peak rain chance over the next ${Number(forecast.lookahead_hours || 0)} hours.`;
  elements.forecastSummary.textContent = `Peak rain chance: ${Math.round(Number(forecast.max_precipitation_probability || 0))}% • Expected precipitation: ${Number(forecast.total_precipitation || 0).toFixed(2)} mm over the next ${Number(forecast.lookahead_hours || 0)} hours.`;

  if (!forecast.entries?.length) {
    elements.forecastList.className = "forecast-list empty-state";
    elements.forecastList.textContent = "No forecast available yet.";
  } else {
    elements.forecastList.className = "forecast-list";
    elements.forecastList.innerHTML = forecast.entries
      .slice(0, 6)
      .map(
        (entry) => `
          <article class="forecast-card">
            <div class="forecast-time">${escapeHtml(formatForecastTime(entry.at))}</div>
            <div class="forecast-temp">${entry.temperature == null ? "--" : `${Number(entry.temperature).toFixed(0)} ${escapeHtml(payload.temperature.unit)}`}</div>
            <div class="forecast-meta">Rain chance ${Math.round(Number(entry.precipitation_probability || 0))}%</div>
            <div class="forecast-meta">Precipitation ${Number(entry.precipitation || 0).toFixed(2)} mm</div>
          </article>
        `
      )
      .join("");
  }

  if (!payload.decisions.length) {
    elements.decisionsList.innerHTML = `<div class="empty-state">No rules are configured yet.</div>`;
  } else {
    elements.decisionsList.innerHTML = payload.decisions
      .map((decision) => {
        const cooldownRemaining = Number(decision.cooldown_remaining_seconds);
        const isCooldown = decision.reason === "cooldown_active" && Number.isFinite(cooldownRemaining);
        const cooldownSuffix = isCooldown
          ? ` <span class="decision-cooldown" data-remaining-seconds="${escapeAttribute(cooldownRemaining)}" data-captured-at-ms="${escapeAttribute(Date.now())}">(${formatRemaining(cooldownRemaining)} remaining)</span>`
          : "";
        return `
          <article class="decision-card">
            <div class="decision-card-header">
              <div class="decision-title">${escapeHtml(decision.rule_name)}</div>
              <span class="pill ${decision.action === "start" ? "valid" : decision.action === "stop" ? "invalid" : ""}">${escapeHtml(decision.action)}</span>
            </div>
            <div class="decision-reason">${escapeHtml(decision.reason)}${cooldownSuffix}</div>
            <div class="device-meta mono">device=${escapeHtml(decision.device_id)} • station=${escapeHtml(String(decision.station))}</div>
          </article>
        `;
      })
      .join("");
  }

  const history = payload.recent_history || [];
  if (!history.length) {
    elements.historyList.className = "history-list empty-state";
    elements.historyList.textContent = "No watering runs recorded yet.";
  } else {
    elements.historyList.className = "history-list";
    elements.historyList.innerHTML = history
      .map((entry) => {
        const isProgram = entry.source === "program";
        const label = isProgram
          ? (entry.rule_name ? escapeHtml(entry.rule_name) : "Program")
          : "Controller";
        const sourceTag = isProgram ? "program" : "controller";
        const time = entry.started_at ? new Date(entry.started_at).toLocaleString() : "Unknown time";
        return `
          <article class="history-card">
            <div class="history-card-header">
              <div class="history-label">${label}</div>
              <span class="pill history-source-${sourceTag}">${isProgram ? "Program" : "Controller"}</span>
            </div>
            <div class="history-meta mono">station ${escapeHtml(String(entry.station))} • ${escapeHtml(time)}</div>
          </article>
        `;
      })
      .join("");
  }
}

function describeDelayStatus(delayStatus) {
  if (delayStatus.manual_active && delayStatus.automatic_active) {
    return "Manual + forecast";
  }
  if (delayStatus.manual_active) {
    return "Manual delay";
  }
  if (delayStatus.automatic_active) {
    return "Forecast delay";
  }
  return "No delay";
}

function describeAutomationStatus(status) {
  if (!status || !status.running) {
    return "Live automation is not running.";
  }
  if (status.last_cycle_error) {
    return `Live automation is running, but the last cycle failed: ${status.last_cycle_error}`;
  }
  const interval = Number(status.poll_interval_seconds || 0);
  if (interval > 0) {
    return `Live automation is active and checks rules every ${interval} seconds.`;
  }
  return "Live automation is active while this web UI is open.";
}

function formatForecastTime(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Unknown time";
  }
  return parsed.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function renderActiveWatering() {
  if (!state.activeWatering.length) {
    elements.activeWateringList.className = "active-watering-list empty-state";
    elements.activeWateringList.textContent = "No active stations right now.";
    return;
  }

  elements.activeWateringList.className = "active-watering-list";
  elements.activeWateringList.innerHTML = state.activeWatering
    .map((entry) => {
      const isProgram = entry.source === "program";
      const isTimer = entry.source === "timer";
      const title = `${escapeHtml(entry.device_name)} • station ${escapeHtml(String(entry.station))}`;
      const tag = isProgram ? "Program" : isTimer ? "Timer" : "Controller";
      const secondary = isProgram
        ? (entry.rule_name ? `Rule: ${escapeHtml(entry.rule_name)}` : "Program initiated")
        : isTimer ? "BHyve timer-initiated run" : "Controller-initiated run";
      const sourceTag = isProgram ? "history-source-program" : isTimer ? "history-source-timer" : "history-source-controller";

      const remaining = isProgram && entry.ends_at
        ? `<div class="active-remaining mono" data-end-at="${escapeAttribute(entry.ends_at)}"></div>`
        : `<div class="active-remaining mono">Time remaining unavailable</div>`;

      return `
        <article class="active-watering-card ${isProgram ? "active-program" : isTimer ? "active-timer" : "active-controller"}">
          <div class="active-watering-header">
            <div class="active-watering-title"><span class="active-dot"></span>${title}</div>
            <span class="pill ${sourceTag}">${tag}</span>
          </div>
          <div class="active-watering-meta">${secondary}</div>
          ${remaining}
        </article>
      `;
    })
    .join("");

  updateActiveWateringCountdowns(new Date());
}

function updateActiveWateringCountdowns(now = new Date()) {
  if (!elements.activeWateringList) {
    return;
  }
  elements.activeWateringList.querySelectorAll("[data-end-at]").forEach((node) => {
    const value = node.getAttribute("data-end-at");
    const parsed = value ? new Date(value) : null;
    if (!parsed || Number.isNaN(parsed.getTime())) {
      node.textContent = "Time remaining unavailable";
      return;
    }

    const seconds = Math.max(0, Math.ceil((parsed.getTime() - now.getTime()) / 1000));
    node.textContent = seconds > 0
      ? `Program time remaining: ${formatRemaining(seconds)}`
      : "Program run is ending now";
  });
}

function formatRemaining(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function renderManualDeviceOptions() {
  const currentDeviceId = elements.manualDevice.value;
  if (!state.devices.length) {
    elements.manualDevice.innerHTML = `<option value="">Load devices first</option>`;
    elements.manualStation.innerHTML = `<option value="">No zones</option>`;
    return;
  }

  elements.manualDevice.innerHTML = state.devices
    .map((device) => `<option value="${escapeAttribute(device.id)}">${escapeHtml(device.name)} (${escapeHtml(device.id)})</option>`)
    .join("");

  if (state.devices.some((device) => device.id === currentDeviceId)) {
    elements.manualDevice.value = currentDeviceId;
  }
  syncManualStations();
}

function syncManualStations() {
  const selectedDevice = state.devices.find((device) => device.id === elements.manualDevice.value) || state.devices[0];
  if (!selectedDevice) {
    elements.manualStation.innerHTML = `<option value="">No zones</option>`;
    return;
  }
  elements.manualStation.innerHTML = (selectedDevice.zones || [])
    .map((zone) => `<option value="${escapeAttribute(zone.station)}">${escapeHtml(zone.name)} (station ${escapeHtml(String(zone.station))})</option>`)
    .join("");
}

async function startManualWatering() {
  try {
    const deviceId = elements.manualDevice.value;
    const station = Number(elements.manualStation.value);
    const minutes = Number(elements.manualMinutes.value || 5);
    const payload = await apiRequest("/api/manual-water", {
      method: "POST",
      body: JSON.stringify({ device_id: deviceId, station, minutes }),
    });
    setBanner(elements.manualStatus, payload.message, "success");
    await previewDecisions({ saveConfigFirst: false, automatic: false });
  } catch (error) {
    setBanner(elements.manualStatus, error.message, "error");
  }
}

async function stopManualWatering() {
  try {
    const deviceId = elements.manualDevice.value;
    const payload = await apiRequest("/api/stop-water", {
      method: "POST",
      body: JSON.stringify({ device_id: deviceId }),
    });
    setBanner(elements.manualStatus, payload.message, "success");
    await previewDecisions({ saveConfigFirst: false, automatic: false });
  } catch (error) {
    setBanner(elements.manualStatus, error.message, "error");
  }
}

function setBanner(element, message, tone = "muted") {
  element.textContent = message;
  element.className = `status-banner ${tone}`;
}

function optionalNumber(value) {
  return value === "" ? null : Number(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value ?? "");
}

async function lookupLocation() {
  const query = elements.locationQuery.value.trim();
  if (query.length < 2) {
    setBanner(elements.locationStatus, "Enter at least two characters to search for a location.", "error");
    return;
  }

  try {
    const payload = await apiRequest(`/api/geocode?query=${encodeURIComponent(query)}`);
    renderLocationResults(payload.results);
    setBanner(
      elements.locationStatus,
      payload.results.length
        ? `Found ${payload.results.length} location match(es).`
        : "No locations matched that search.",
      payload.results.length ? "success" : "muted",
    );
  } catch (error) {
    setBanner(elements.locationStatus, error.message, "error");
  }
}

function renderLocationResults(results) {
  if (!results.length) {
    elements.locationResults.innerHTML = `<div class="empty-state">No location matches found.</div>`;
    return;
  }

  elements.locationResults.innerHTML = results
    .map(
      (result, index) => `
        <article class="location-card">
          <div>
            <div class="location-name">${escapeHtml(result.name)}</div>
            <div class="device-meta">${escapeHtml([result.admin1, result.country].filter(Boolean).join(", ") || "Unknown region")}</div>
            <div class="device-meta mono">lat=${escapeHtml(String(result.latitude))} • lon=${escapeHtml(String(result.longitude))}</div>
            <div class="device-meta">Timezone: ${escapeHtml(result.timezone || "unknown")}</div>
          </div>
          <div class="location-actions">
            <button class="button button-primary" type="button" data-location-index="${index}">Use Coordinates</button>
          </div>
        </article>
      `
    )
    .join("");

  elements.locationResults.querySelectorAll("[data-location-index]").forEach((button) => {
    button.addEventListener("click", () => {
      const result = results[Number(button.dataset.locationIndex)];
      elements.weatherLatitude.value = result.latitude;
      elements.weatherLongitude.value = result.longitude;
      setBanner(
        elements.locationStatus,
        `Applied coordinates for ${result.name}. Save config when you are ready.`,
        "success",
      );
    });
  });
}

async function applyManualWeatherDelay() {
  const hours = Math.max(1, Number(elements.manualDelayHours.value || 0));
  if (!state.config) {
    setBanner(elements.previewStatus, "Load the config before applying a weather delay.", "error");
    return;
  }

  try {
    const config = collectConfigFromForm();
    config.controller.manual_weather_delay_until = new Date(Date.now() + hours * 60 * 60 * 1000).toISOString();
    await persistConfig(config, { runImmediateAutomation: false });
    await previewDecisions({ saveConfigFirst: false, automatic: false });
    setBanner(elements.previewStatus, `Manual weather delay applied for ${hours} hour(s).`, "success");
  } catch (error) {
    setBanner(elements.previewStatus, error.message, "error");
  }
}

async function clearManualWeatherDelay() {
  if (!state.config) {
    setBanner(elements.previewStatus, "Load the config before clearing a weather delay.", "error");
    return;
  }

  try {
    const config = collectConfigFromForm();
    config.controller.manual_weather_delay_until = null;
    await persistConfig(config, { runImmediateAutomation: false });
    await previewDecisions({ saveConfigFirst: false, automatic: false });
    setBanner(elements.previewStatus, "Manual weather delay cleared.", "success");
  } catch (error) {
    setBanner(elements.previewStatus, error.message, "error");
  }
}

function updateDecisionCooldownCountdowns(now = new Date()) {
  if (!elements.decisionsList) {
    return;
  }

  elements.decisionsList.querySelectorAll(".decision-cooldown").forEach((node) => {
    const baseValue = Number(node.getAttribute("data-remaining-seconds"));
    const capturedAtMs = Number(node.getAttribute("data-captured-at-ms"));
    if (!Number.isFinite(baseValue) || !Number.isFinite(capturedAtMs)) {
      return;
    }

    const elapsedSeconds = Math.max(0, Math.floor((now.getTime() - capturedAtMs) / 1000));
    const remainingSeconds = Math.max(0, baseValue - elapsedSeconds);
    node.textContent = remainingSeconds > 0
      ? `(${formatRemaining(remainingSeconds)} remaining)`
      : "(ending now)";
  });
}