# Bhyve Temperature Controller

This project adds temperature-driven manual watering on top of Orbit BHyve without editing or disabling the schedules you already configured in the BHyve app.

## What it does

- Polls current weather from Open-Meteo and now includes short-range forecast risk for dashboard status and delay decisions.
- Reads your BHyve devices and zones from Orbit's cloud API.
- Starts a temporary manual zone run only when a rule is hot enough, no watering is already active, and the next built-in schedule is not too close.
- Stops only the manual runs started by this script when the temperature cools below the stop threshold.

The controller never updates your native BHyve timer programs. It only sends temporary websocket commands for manual watering.

## Files

- `main.py`: CLI entry point.
- `bhyve_app/web_ui.py`: Local `aiohttp` web UI and API endpoints.
- `bhyve_app/bhyve_client.py`: Minimal Orbit BHyve REST and websocket client.
- `bhyve_app/controller.py`: Temperature decision logic and service loop.
- `bhyve_app/weather.py`: Open-Meteo temperature client.
- `config.example.json`: Starter configuration.
- `launch_web_ui.bat`: Quick launcher for the web setup screen.

## Setup

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Create a real `config.json` from `config.example.json`.
3. Set your BHyve password in an environment variable:

```powershell
$env:BHYVE_PASSWORD = "your-password"
```

4. List your devices and zone station numbers:

```powershell
python main.py devices --config config.json
```

5. Update the rule entries in `config.json` with the correct `device_id` and `station` values.

If you would rather not edit JSON by hand, launch the web UI and do the same setup in the browser.

## Web UI

Launch the local web UI:

```powershell
python main.py --config config.json web --host 0.0.0.0 --open-browser
```

Or use the helper batch file:

```bat
launch_web_ui.bat
```

The web UI helps with:

- filling out BHyve account, weather, and controller defaults
- translating city or location searches into latitude and longitude
- building and editing rules without hand-editing JSON
- discovering device IDs and zone station numbers from Orbit BHyve
- showing a status-first dashboard with current conditions, forecast cards, next trigger timing, and controller delay state
- previewing dry-run decisions before enabling live control
- applying or clearing a manual weather delay directly from the dashboard
- sending manual start and stop commands to a zone for testing

Sensor ingest supports three paths that all use the same JSON schema:

- HTTP: `POST /api/sensors`
- Serial bus: newline-delimited JSON frames (for example from ESP32 over USB serial)
- Bluetooth LE: notification payloads containing UTF-8 JSON

Enable serial and/or BLE ingest in `config.json` under `ingest.serial` and `ingest.bluetooth`.
Each frame/payload should be a JSON object using the same fields as `/api/sensors`, for example:

```json
{"device_id":"device-123","station":1,"soil_moisture_percent":32,"motion_detected":false}
```

When the web UI server is running, it also runs the live temperature controller loop in the background using your configured poll interval. You do not need to run `run.bat` or `python main.py run` at the same time.

## Google Sign-In Accounts

Orbit's private API surface used by this project still exposes session and API-token auth, not a documented Google OAuth flow. For accounts that sign in to BHyve with Google, use the web UI's `Orbit API token (Google sign-in)` mode and paste the `orbit_api_key` from an authenticated Orbit dashboard session.

## Commands

List devices and zones:

```powershell
python main.py devices --config config.json
```

Preview a single control cycle without changing anything:

```powershell
python main.py status --config config.json
```

Run one live control cycle:

```powershell
python main.py run --config config.json --once
```

Run continuously:

```powershell
python main.py run --config config.json
```

Run the local web UI:

```powershell
python main.py --config config.json web --host 0.0.0.0 --port 8787 --open-browser
```

To open the dashboard from your phone, connect the phone to the same local network and browse to the LAN URL printed in the app logs, for example `http://192.168.1.42:8787`.

Manually start a zone for testing:

```powershell
python main.py water --config config.json --device-id YOUR_DEVICE_ID --station 1 --minutes 5
```

`--minutes` also accepts decimal values. For example, `--minutes 0.5` starts a 1-minute Orbit run and then sends a stop command after about 30 seconds.

Stop a manual run on a device:

```powershell
python main.py stop --config config.json --device-id YOUR_DEVICE_ID
```

## Rule behavior

Each rule uses hysteresis so the controller does not flap on every small temperature change:

- `start_above`: starts a manual run once the temperature reaches or exceeds this threshold.
- `stop_below`: stops the script-owned run once the temperature drops to or below this threshold.
- `schedule_guard_minutes`: prevents the script from starting a manual run right before a native BHyve schedule begins.
- `manual_run_minutes`: accepts positive decimal values such as `0.5`; the app rounds the Orbit start request up to a full minute and then sends a stop command at the requested second mark.
- `cooldown_minutes`: minimum delay before the same rule can trigger again.
- `max_runs_per_day`: caps how many extra runs the script can start for a zone each day.
- `automatic_weather_delay_enabled`: turns forecast-based delay gating on or off.
- `automatic_weather_delay_probability_threshold`: pauses controller-owned watering when the forecast rain chance meets or exceeds this percentage.
- `automatic_weather_delay_lookahead_hours`: how far ahead the controller checks forecast rain probability.
- `manual_weather_delay_until`: an ISO timestamp the dashboard uses to pause controller-owned watering until a specific time.

## Current assumptions

- Weather comes from Open-Meteo using latitude and longitude.
- The BHyve cloud API and websocket protocol are unofficial and reverse engineered by the community.
- One device should only have one script-managed manual run started per control cycle.

Test with a single zone first before expanding rules.
