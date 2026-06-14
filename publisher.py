"""
Publisher for the ABB-gateway simulator feed
============================================
This sits on top of `simulator.py`. The simulator's job is to GENERATE
records; this file's job is to PUBLISH them somewhere.

Stage 1 (current):  ConsolePublisher - just prints each record.
Stage 2 (planned):  MqttPublisher    - push each record to an MQTT broker
                                        so downstream NexOps services can
                                        subscribe. This is a STUB ONLY here;
                                        no real broker connection is made.

The record-pulling logic lives entirely in the simulator: we import
`generate_next_record` and feed whatever it returns into the selected
publisher. We never reach into the simulator's internals or duplicate its
schema.
"""

import json
import time

from simulator import generate_next_record, INTERVAL_SECONDS

# ----------------------------------------------------------------------
# CONFIG  (edit here, not inline below)
# ----------------------------------------------------------------------

# Which publisher to use: "console" (default) or "mqtt".
PUBLISHER = "console"

# How long to run. None = run forever, or set an integer record limit.
TOTAL_RECORDS = None

# Seconds between records. Defaults to the simulator's own interval so the
# feed rate matches `python simulator.py`.
PUBLISH_INTERVAL_SECONDS = INTERVAL_SECONDS

# --- MQTT broker settings (used in Stage 2, ignored by ConsolePublisher) ---
MQTT_HOST = "localhost"      # broker hostname / IP
MQTT_PORT = 1883             # broker port (1883 = plain MQTT, 8883 = TLS)
MQTT_TOPIC = "nexops/refinery/telemetry"   # topic records are published to

# ----------------------------------------------------------------------
# Optional dependency guard
# Stage 2 needs paho-mqtt. Guard the import so this file still runs (with
# ConsolePublisher) even when paho-mqtt is not installed.
# ----------------------------------------------------------------------

try:
    import paho.mqtt.client as mqtt   # noqa: F401  (used in Stage 2)
    _HAS_PAHO = True
except ImportError:
    mqtt = None
    _HAS_PAHO = False


# ----------------------------------------------------------------------
# Publisher interface + implementations
# ----------------------------------------------------------------------

class Publisher:
    """Base interface. A publisher takes a record dict and sends it out."""

    def publish(self, record):
        raise NotImplementedError

    def close(self):
        """Release any resources (connections, sockets). No-op by default."""
        pass


class ConsolePublisher(Publisher):
    """Stage 1 publisher: print each record as a JSON line to stdout."""

    def publish(self, record):
        print(json.dumps(record))


class MqttPublisher(Publisher):
    """Stage 2 publisher: push each record to an MQTT broker.

    *** STUB ONLY - no real MQTT logic yet. ***
    The method bodies below describe what WILL happen and mark every place
    that needs real paho-mqtt code with a TODO.
    """

    def __init__(self, host=MQTT_HOST, port=MQTT_PORT, topic=MQTT_TOPIC):
        self.host = host
        self.port = port
        self.topic = topic
        self.client = None
        # TODO(Stage 2): fail clearly if paho-mqtt is missing.
        #   if not _HAS_PAHO:
        #       raise RuntimeError("paho-mqtt not installed; see requirements.txt")
        # TODO(Stage 2): create the client and connect to the broker, e.g.
        #   self.client = mqtt.Client()
        #   self.client.connect(self.host, self.port)
        #   self.client.loop_start()
        raise NotImplementedError(
            "MqttPublisher is a Stage 2 stub. Implement the paho-mqtt "
            "connection (see TODOs) before selecting PUBLISHER = 'mqtt'."
        )

    def publish(self, record):
        # TODO(Stage 2): publish the record to the broker, e.g.
        #   payload = json.dumps(record)
        #   self.client.publish(self.topic, payload)
        raise NotImplementedError

    def close(self):
        # TODO(Stage 2): cleanly stop the loop and disconnect, e.g.
        #   self.client.loop_stop()
        #   self.client.disconnect()
        pass


# ----------------------------------------------------------------------
# Publisher selection
# ----------------------------------------------------------------------

def make_publisher(name=PUBLISHER):
    """Return a publisher instance for the configured name.
    Defaults to ConsolePublisher for any unknown value."""
    if name == "mqtt":
        return MqttPublisher(MQTT_HOST, MQTT_PORT, MQTT_TOPIC)
    return ConsolePublisher()


# ----------------------------------------------------------------------
# Main loop: pull records from the simulator, send them to the publisher
# ----------------------------------------------------------------------

def main():
    publisher = make_publisher(PUBLISHER)
    print(f"Publishing simulator feed via {type(publisher).__name__} "
          f"(every {PUBLISH_INTERVAL_SECONDS}s). Press CTRL+C to stop.")

    alarm_id = 1
    try:
        while TOTAL_RECORDS is None or alarm_id <= TOTAL_RECORDS:
            record = generate_next_record(alarm_id)
            publisher.publish(record)
            alarm_id += 1
            time.sleep(PUBLISH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nPublisher stopped by user.")
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
