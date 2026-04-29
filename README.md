# weclapp Wareneingang App

## Railway Deployment

### Umgebungsvariablen (in Railway setzen):

| Variable | Beschreibung | Beispiel |
|----------|-------------|---------|
| `WECLAPP_TENANT` | weclapp Tenant URL | `meinshop.weclapp.com` |
| `WECLAPP_API_KEY` | weclapp API Key | `xxxx-xxxx-xxxx` |
| `EMAIL_FROM` | Absender E-Mail | `app@gmail.com` |
| `EMAIL_TO` | Empfänger E-Mail | `chef@firma.de` |
| `EMAIL_USER` | SMTP Benutzername | `app@gmail.com` |
| `EMAIL_PASS` | Gmail App-Passwort | `xxxx xxxx xxxx xxxx` |
| `EMAIL_SMTP` | SMTP Server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP Port | `465` |

### Deployment Schritte:

1. GitHub Repository erstellen
2. Diese Dateien hochladen:
   - `wareneingang.py`
   - `requirements.txt`
   - `Procfile`
3. Railway → New Project → Deploy from GitHub
4. Umgebungsvariablen setzen
5. Deploy!

### Lokaler Start:
```
python wareneingang.py
```
