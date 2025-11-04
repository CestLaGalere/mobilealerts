# Device Type Detection

## Automatische Geräte-Typ-Erkennung

Die Mobile Alerts Integration erkennt automatisch den Gerätetyp basierend auf den verfügbaren Messwerten, die vom API zurückgegeben werden.

## Wie es funktioniert

1. **Benutzer fügt Device hinzu**: Benutzer gibt die Device-ID ein
2. **API Validierung**: Wir fetchen Daten vom API um zu überprüfen, dass die Device-ID gültig ist
3. **Typ-Erkennung**: Wir analysieren die Messwerte um zu ermitteln welcher Gerätetyp es ist
4. **Sensoren-Erstellung**: Basierend auf dem erkannten Typ werden nur die passenden Sensoren erstellt

## Erkannte Gerätetypen

| ID   | Name                                | Messwerte      | Primärer Typ |
| ---- | ----------------------------------- | -------------- | ------------ |
| ID01 | Thermometer mit Kabelsensor         | t1, t2         | t2           |
| ID02 | Thermometer                         | t1             | t1           |
| ID03 | Thermo-/Hygrometer                  | t1, h          | h            |
| ID04 | Thermo-/Hygrometer mit Kabelsensor  | t1, t2, h      | t2           |
| ID05 | Thermo-/Hygrometer mit Luftqualität | t1, t2, h, ppm | ppm          |
| ID06 | Thermo-/Hygrometer mit Kabelsensor  | t1, t2, h      | t2           |
| ID07 | Dual Thermo-/Hygrometer             | t1, t2, h, h2  | h2           |
| ID08 | Regenmesser                         | t1, r, rf      | r            |
| ID09 | Thermo-/Hygrometer mit Kabelsensor  | t1, t2, h      | t2           |
| ID0A | Thermometer mit Rauchmelder         | t1, a1-a4      | t1           |
| ID0B | Windmesser                          | ws, wg, wd     | ws           |
| ID0E | Thermo-/Hygrometer                  | t1, h          | h            |
| ID0F | Thermometer mit Kabelsensor         | t1, t2         | t2           |
| ID10 | Fenster/Türsensor                   | w              | w            |
| ID11 | Multi-Sensor (4x Temp, 4x Hum)      | t1-t4, h1-h4   | t1           |
| ID12 | Thermo-/Hygrometer mit Averages     | t1, h, h\*avg  | h            |
| ID15 | Funkschalter                        | kp1t-kp4t, ... | sc           |
| ID17 | Klima-Steuerung                     | t1, t2         | t2           |
| ID18 | Thermo-/Hygrometer/Barometer        | t1, h, ap      | ap           |
| ID20 | Thermometer                         | t1             | t1           |

## Sensoren pro Gerätetyp

Abhängig vom erkannten Typ werden folgende Sensoren erstellt:

### t1 (Temperatur)

- ✅ Temperature
- ✅ Battery
- ✅ Last Seen

### t2 (Temperatur mit Kabelsensor)

- ✅ Temperature
- ✅ Cable Temperature
- ✅ Battery
- ✅ Last Seen

### h (Feuchtigkeit)

- ✅ Temperature
- ✅ Humidity
- ✅ Battery
- ✅ Last Seen

### h2 (Externe Feuchtigkeit)

- ✅ Temperature
- ✅ Cable Temperature
- ✅ Humidity
- ✅ External Humidity
- ✅ Battery
- ✅ Last Seen

### r (Regen)

- ✅ Temperature
- ✅ Rain
- ✅ Battery
- ✅ Last Seen

### ws (Wind)

- ✅ Wind Speed
- ✅ Wind Gust
- ✅ Battery
- ✅ Last Seen

### ap (Luftdruck)

- ✅ Temperature
- ✅ Humidity
- ✅ Pressure
- ✅ Battery
- ✅ Last Seen

### ppm (Luftqualität)

- ✅ Temperature
- ✅ Cable Temperature
- ✅ Humidity
- ✅ Air Quality
- ✅ Battery
- ✅ Last Seen

### w (Fenster/Tür)

- ✅ Window Status
- ✅ Battery
- ✅ Last Seen

## Fehlgeschlagene Erkennung

Falls der Gerätetyp nicht erkannt werden kann (z.B. neues Gerät mit unbekannter Messwert-Kombination):

- Es werden nur **Battery** und **Last Seen** Sensoren erstellt
- Dies verhindert Fehler durch unbekannte Sensoren
- Der Benutzer sollte ein Update der Integration durchführen

## Implementierung

Die Erkennung erfolgt in `const.py` in der Funktion `detect_device_type()`:

```python
from custom_components.mobile_alerts.const import detect_device_type

measurement = {...}  # API response measurement
device_type = detect_device_type(measurement)
```
