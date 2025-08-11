# Flask Credential Issuing App

Diese Flask-Anwendung ermöglicht das Hochladen von CSV-Dateien, die Verarbeitung der enthaltenen Personendaten, die Erstellung und Ausstellung von digitalen Credentials über eine externe API sowie die Anzeige und Suche von Personen mit generierten QR-Codes.

---

## Endpunkte (Routes)

### `/` - Upload und Verarbeitung von CSV-Dateien

**Methoden:** `GET`, `POST`

- **Beschreibung:**  
  Diese Route stellt ein Formular bereit, mit dem Nutzer eine CSV-Datei hochladen können. Die CSV-Datei wird eingelesen und in JSON umgewandelt.  
  Anschließend wird für die erste Person in der CSV-Datei ein Credential bei der externen Procivis-API erstellt und ausgestellt. Die Credential-Daten werden in der lokalen Datenbank gespeichert.

- **Funktionsweise:**  
  - Upload einer CSV-Datei mit dem Formular (nur `.csv` Dateien akzeptiert).
  - Die Datei wird eingelesen und in ein JSON-ähnliches Python-Objekt konvertiert.
  - Über eine API-Verbindung zu `api.trial.procivis-one.com` wird ein Credential mit den Daten der ersten Person erstellt.
  - Das ausgestellte Credential enthält eine URL, die in der Datenbank mit Name und Nachname der Person gespeichert wird.
  - Alle Personen aus der CSV werden in der Datenbank gespeichert.

- **Fehlerbehandlung:**  
  Bei Fehlern (z.B. beim API-Aufruf) wird eine JSON-Antwort mit Fehlermeldung zurückgegeben.

---

### `/people` - Anzeige aller Personen

**Methoden:** `GET`

- **Beschreibung:**  
  Zeigt eine Liste aller in der Datenbank gespeicherten Personen an.

- **Details:**  
  - Lädt alle `Person`-Einträge aus der SQLite-Datenbank.
  - Rendert die `people.html`-Vorlage mit der Liste der Personen.

---

### `/identification` - Suche und Weiterleitung zu QR-Code

**Methoden:** `GET`, `POST`

- **Beschreibung:**  
  Bietet ein Formular, in dem der Nutzer Name und Nachname eingeben kann, um nach einer Person zu suchen.

- **Funktionsweise:**  
  - Bei `GET`: Zeigt das Formular zur Eingabe von Name und Nachname.
  - Bei `POST`: Sucht die Person in der Datenbank (case-insensitive Suche).
  - Wird die Person gefunden, erfolgt eine Weiterleitung zur QR-Code-Seite (`/qr/<person_id>`).
  - Falls keine Person gefunden wird, wird das Formular erneut mit einer Fehlermeldung angezeigt.

---

## Datenbankmodell: `Person`

| Feld    | Typ           | Beschreibung                  |
|---------|---------------|------------------------------|
| `id`    | Integer (PK)  | Primärschlüssel               |
| `name`  | String(100)   | Vorname                      |
| `surname` | String(100) | Nachname                     |
| `url`   | String(300)   | URL zum ausgestellten Credential (für QR-Code) |

---

## Verwendung

1. Starte die Anwendung mit:
   ```bash
   python app.py
2. Besuche im Browser:
/ um eine CSV-Datei hochzuladen und Credentials zu erstellen.
/people um alle gespeicherten Personen zu sehen.
/identification um eine Person per Name und Nachname zu suchen und zum QR-Code weitergeleitet zu werden.

## Hinweise
- Der Upload-Ordner uploads wird automatisch erstellt, falls nicht vorhanden.
- Die externe API benötigt ein gültiges Bearer-Token (aktuell hartcodiert in der App).
- Die CSV-Datei muss bestimmte Feldnamen enthalten, z.B. firstName, officialName, originName etc.
- Die QR-Codes werden als Base64-encoded PNG-Bilder in der HTML-Seite eingebe
