# nexops-data-generator

A stand-in **ABB gateway** for the NexOps prototype. Real ABB 800xA gateways
stream live process telemetry and alarms off refinery equipment; this service
fakes that feed so the rest of NexOps can be built and demoed without the real
hardware.

It produces a realistic, noisy, **escalating** stream of sensor readings and
alarms across 16 refinery assets (compressors, pumps, boilers, fired heaters,
reactors, etc.), including slow *predictive* degradation faults that drift below
the static alarm limit before they trip — the centrepiece for demonstrating
early anomaly detection.

## Components

| File              | Role                                                            |
|-------------------|-----------------------------------------------------------------|
| `simulator.py`    | Generates records. Stdlib only. Run it to print + log the feed. |
| `publisher.py`    | Pulls records from the simulator and publishes them.            |
| `requirements.txt`| Dependencies (Stage 1 needs none).                              |

A consumer pulls records by importing **`generate_next_record(alarm_id, phase=None)`**
from `simulator`. It returns one record dict per call, does no printing or file
writing, and (when `phase` is omitted) derives the demo-escalation phase itself.

## Record schema

Each record is a JSON object with these fields:

| Field               | Meaning                                                  |
|---------------------|----------------------------------------------------------|
| `Machine`           | Asset name (e.g. "Compressor")                           |
| `Timestamp`         | `YYYY-MM-DD HH:MM:SS` local time                          |
| `Temp` / `Pressure` / `Level` / `Flow` | Four common dashboard columns (any may be `null`) |
| `Status`            | `Normal` / `Warning` / `Critical`                        |
| `Alert`             | Short alert label (`None` when normal)                   |
| `features`          | Object of this machine's raw sensor readings             |
| `alarm_id`          | Monotonic tick id                                        |
| `scenario_name`     | Same as the alert label                                  |
| `alarm_type`        | `Process` / `Safety` / `Electrical` / `System` / `Predictive` |
| `alarm_priority`    | `Critical` / `High` / `Medium` / `Low`                   |
| `priority_level`    | Numeric priority (1=Critical … 4=Low)                    |
| `alarm_state`       | Lifecycle: `ACT` / `ACK` / `RTN`                         |
| `ack_state`         | `Unacknowledged` / `Acknowledged`                        |
| `is_predictive`     | `true` for early-warning (below static limit) alarms     |
| `object_name`       | Instrument tag (e.g. "PIC-CMP01")                        |
| `object_description`| Human description of the asset                           |
| `message`           | Full human-readable alarm message                        |

### Example record

```json
{
  "Machine": "Compressor",
  "Timestamp": "2026-06-14 10:23:45",
  "Temp": 58.4,
  "Pressure": 7.82,
  "Level": null,
  "Flow": null,
  "Status": "Normal",
  "Alert": "None",
  "features": {"gen_temp": 58.4, "comp_pressure": 7.82, "vibration": 1.6, "current": 24.3, "rpm": 1493.0},
  "alarm_id": 1,
  "scenario_name": "None",
  "alarm_type": "Process",
  "alarm_priority": "Low",
  "priority_level": 4,
  "alarm_state": "RTN",
  "ack_state": "Acknowledged",
  "is_predictive": false,
  "object_name": "PIC-CMP01",
  "object_description": "Process Gas Compressor Discharge",
  "message": "All parameters within normal operating range"
}
```

## Running

### Simulator (prints rows + appends JSONL)

```bash
python simulator.py
```

Prints a live formatted table and appends each record as one JSON line to
`refinery_live_data.jsonl`. Press **CTRL+C** to stop.

### Publisher (Stage 1: console)

```bash
python publisher.py
```

Pulls records from the simulator and prints each as a JSON line via the default
`ConsolePublisher`. Press **CTRL+C** to stop. Configuration (publisher choice,
interval, broker settings) lives in the `CONFIG` block at the top of
`publisher.py`.

## Stage 2: enable MqttPublisher (not done yet)

`MqttPublisher` in `publisher.py` is currently a **stub** — method signatures
and `TODO` comments only, with no real broker connection. To enable it later:

1. Uncomment `paho-mqtt` in `requirements.txt` and `pip install -r requirements.txt`.
2. Implement the `TODO(Stage 2)` blocks in `MqttPublisher` (connect / publish / close).
3. Set the broker target in the CONFIG block: `MQTT_HOST`, `MQTT_PORT`, `MQTT_TOPIC`.
4. Set `PUBLISHER = "mqtt"`.
