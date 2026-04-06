# Tizen Remastered

Neue Home-Assistant-Custom-Integration fuer Samsung-Tizen-Fernseher.

## Aktueller Stand

- Moderne Config-Entry-Basis mit `config_flow`
- `media_player`-Entity fuer den Fernseher
- `select`-Entity fuer Quellen
- optionale `select`-Entity fuer Apps
- Lokaler Statuscheck ueber `http://<tv-ip>:8001/api/v2/`
- Grundlegende Steuerung fuer:
  - Ein
  - Aus
  - Lauter / Leiser
  - Mute
  - Play / Pause / Stop
  - Kanal vor / zurueck
  - Quellenwahl fuer TV und HDMI
  - Key senden ueber `media_player.play_media`
  - App starten
  - URL im Browser oeffnen

## Struktur

- `custom_components/tizen_remastered/manifest.json`
- `custom_components/tizen_remastered/config_flow.py`
- `custom_components/tizen_remastered/coordinator.py`
- `custom_components/tizen_remastered/client.py`
- `custom_components/tizen_remastered/media_player.py`
- `custom_components/tizen_remastered/select.py`

## App-Liste

Damit in Home Assistant eine App-Auswahl erscheint, kann im Config-Flow eine JSON-App-Liste hinterlegt werden, zum Beispiel:

```json
{"YouTube":"111299001912","Netflix":"11101200001","Prime Video":"3201512006785"}
```

## configuration.yaml

`api_key` und `device_id` koennen ueber die `configuration.yaml` vorgegeben werden. Beispiel:

```yaml
tizen_remastered:
  - host: 192.168.178.69
    name: Samsung TV Remastered
    port: 8002
    ws_name: Home Assistant
    mac: "68:72:c3:60:dd:49"
    api_key: "DEIN_SMARTTHINGS_API_KEY"
    device_id: "DEINE_SMARTTHINGS_DEVICE_ID"
    app_list: '{"YouTube":"111299001912","Netflix":"11101200001"}'
```
