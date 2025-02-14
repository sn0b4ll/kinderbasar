# Beschreibung
Diese Applikation hilft bei der Organisation von Vor-Ort Basaren. Funktionen:
- Einstellen von Artikeln durch Verkäufer
- Generierung von Etiketten für Artikel durch Verkäufer
- Kassen-System über Etiketten für ein schnelles kassieren
- Generierung von Listen für die Wahren-Annahme
- Übersichts-Funktionen für Organisatoren

# Wie startet man die Anwendung
Die Web-Anwendung ist in Python geschrieben und greift auf eine MySQL-Datenbank zurück. Jedoch kann der Start einfach über 'docker compose' realisiert werden.

1. Die Datei '.env.conf' im 'conf'-Verzeichnis kopieren und als 'env.conf' im 'conf'-Verzeichnis ablegen.
2. Die Inhalte der 'env.conf' anpassen auf das eigene Setup
3. Im 'docker-compose.yml' die Konfiguration prüfen und ports anpassen.
4. Es wird empfohlen über einen Reverse-Proxy wie nginx das TLS-Handling zu realisieren und den Flask-Port nicht direkt für den Zugriff von außen freigeben
5. Über 'docker compose up -d' die Anwendung starten. Da zuerst die Datenbank initialisiert wird, kann das beim ersten mal bis zu 5 Minuten dauern.

# Entwicklung
## Rebuild and start application
- Remove old containers
`docker compose stop`
`docker compose rm`

- Rebuild containers
`docker compose build`

- Start containers
`docker compose up --force-recreate --remove-orphans`