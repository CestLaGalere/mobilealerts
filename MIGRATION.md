# Mobile Alerts Integration - Migration Guide

## Automatische Migration (Neue Version)

Wenn Sie ein Update von der alten YAML-basierten Konfiguration durchführen, läuft die Migration **automatisch** ab.

### 📋 Migration Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Home Assistant startet mit alter config.yaml             │
│    └─ mobile_alerts: Platform geladen                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Neue Version wird installiert                            │
│    └─ __init__.py erkennt YAML-Config                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Home Assistant wird neu gestartet                        │
│    └─ __init__.py triggert Config Flow Import               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Config Flow - Import Step                                │
│    └─ YAML-Konfiguration wird geparst                       │
│    └─ Devices aus YAML werden extrahiert                    │
│    └─ Neue ConfigEntry wird erstellt                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Integration Setup                                        │
│    └─ __init__.py: async_setup_entry() wird aufgerufen     │
│    └─ sensor.py: Sensoren werden aus ConfigEntry erstellt   │
│    └─ Alte YAML wird IGNORIERT (async_setup_platform)      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Migrationsabschluss                                      │
│    ✅ Sensoren funktionieren mit neuen Entity-IDs           │
│    ✅ Dashboard/Automationen arbeiten normal weiter         │
│    ⚠️  Benutzer sollte YAML-Config entfernen                │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Entity-IDs bleiben gleich

Die unique_id wird wie folgt generiert:

```python
unique_id = f"{device_id}_{sensor_key}"

# Beispiel:
# device_id: "034408A9B313"
# sensor_key: "temperature"
# unique_id: "034408A9B313_temperature"
```

**Wichtig**: Die unique_id ist **gleich geblieben**, daher bleiben die entity_ids identisch:

- `sensor.schlafzimmer_eg_temp` (vorher)
- `sensor.schlafzimmer_eg_temp` (nachher) ✅

## ⚠️ Nach der Migration

### ✅ Automatische YAML-Entfernung (NEU!)

Die YAML-Konfiguration wird **automatisch behandelt**:

1. **Import Flow erkennt YAML**
2. **ConfigEntry wird erstellt** mit migrierten Devices
3. **YAML wird intern deaktiviert** (nicht mehr geladen)
4. **Log-Meldung** informiert Sie über den Status

```
✅ Log-Meldung nach erfolgreicher Migration:
"YAML configuration will be ignored.
Please remove 'mobile_alerts:' section from configuration.yaml
to complete the migration."
```

### 📋 Manuelle Bereinigung (Optional aber empfohlen):

Obwohl die YAML-Config automatisch ignoriert wird, sollten Sie sie trotzdem entfernen:

1. **Bearbeiten Sie configuration.yaml**:

   ```yaml
   # Entfernen Sie diese Zeilen:
   mobile_alerts:
     phone_id: "123456789"
     devices:
       - device_id: "ABC123"
         name: "Mein Gerät"
         type: "t"
   ```

2. **Home Assistant neu starten** (optional, aber sauberer)

3. **Resultat**: Konfigurationsdatei ist sauber, keine Legacy-Config mehr

### Was passiert, wenn Sie YAML NICHT entfernen?

⚠️ **Keine Probleme!** Die alte YAML wird automatisch ignoriert:

```
Mobile Alerts: Found both YAML configuration and UI ConfigEntry.
YAML will be IGNORED. Please remove 'mobile_alerts:' section
from configuration.yaml to avoid confusion.
```

✅ **Keine Duplikate**:

- Neue Sensoren werden NUR aus ConfigEntry erstellt
- Alte `async_setup_platform()` wird deaktiviert
- YAML wird vom System ignoriert (safe to leave)

## 🆕 Neue Installation (Vereinfacht!)

### Schritt 1: Integration hinzufügen

1. **Settings → Devices & Services → Create Integration**
2. Suchen Sie nach **"mobile_alerts"**
3. Klicken Sie auf **"Mobile Alerts"**
4. Bestätigen Sie - das war's! ✅

### Schritt 2: Geräte hinzufügen

Nach der Installation sehen Sie einen **"Add Device"** Button:

1. Klicken Sie auf **"Add Device"** (oben rechts)
2. Geben Sie die **Device-ID** ein
3. Das Gerät wird sofort hinzugefügt ✅

**Wo finde ich die Device-ID?**

- Öffnen Sie die **Mobile Alerts App**
- Gehen Sie zu **Einstellungen → Meine Geräte**
- Dort finden Sie die **Device-ID** (z.B. "A1B2C3D4E5F6")

### Vorteile dieser neuen Methode:

✅ **Keine Phone-ID nötig!** (Viel einfacher)
✅ Sie kontrollieren genau welche Geräte hinzugefügt werden
✅ Devices können jederzeit über "Add Device" hinzugefügt werden
✅ Einfach und transparent!

## 📝 Häufige Fragen

### F: Werden meine Automationen/Dashboards nach der Migration immer noch funktionieren?

**A**: Ja! Die Entity-IDs ändern sich **nicht**. Alles funktioniert wie vorher.

### F: Was ist mit der Reihenfolge der Sensoren?

**A**: Die Reihenfolge kann sich ändern (z.B. Battery wird jetzt immer zuerst erstellt), aber Sie können Sensoren in der UI neu ordnen.

### F: Kann ich die Migration rückgängig machen?

**A**: Ja, Sie können die ConfigEntry löschen und wieder die YAML-Config nutzen (alte Version).

### F: Wird die YAML-Config automatisch entfernt?

**A**: Die **Konfiguration wird automatisch vom System ignoriert**, nachdem die Migration abgeschlossen ist. Sie können sie manuell aus `configuration.yaml` entfernen (empfohlen für Sauberkeit), aber es ist nicht notwendig.

### F: Sehe ich eine Warnung/Meldung im Log?

**A**: Ja, es gibt eine Info-Meldung:

```
"YAML configuration will be ignored.
Please remove 'mobile_alerts:' section from configuration.yaml
to complete the migration."
```

Das ist **völlig normal** und bedeutet, dass die Migration erfolgreich war.

### F: Was wenn ich YAML und ConfigEntry habe?

**A**: Das ist kein Problem! Die ConfigEntry hat **Priorität**, die YAML wird ignoriert. Sie können die YAML jederzeit entfernen.
