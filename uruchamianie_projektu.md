# Komendy uruchomieniowe projektu (VetClinic + blockchain + observability)


## 1) Start całego klastra w Dockerze (node1..node6 + Prometheus + Grafana)

```powershell
docker compose up -d --build
```

Sprawdzenie, czy wszystko żyje:

```powershell
docker compose ps
```

Wyłączenie (bez kasowania wolumenów):

```powershell
docker compose down --remove-orphans
```

Wyłączenie + skasowanie wolumenów:

```powershell
docker compose down -v --remove-orphans
```

### Dostępy
- Node1 API: http://localhost:8001
- Node2 API: http://localhost:8002
- ...
- Node6 API: http://localhost:8006
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

---

## 2) Szybki test, że blockchain działa (ruch + konsensus)
Submit tx na lidera (node1):

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/tx/submit" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"sender":"alice","recipient":"bob","amount":10.5}'
```

Rozproszony mining / konsensus

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/chain/mine_distributed" -Method POST
```

Weryfikacja height na wszystkich nodach (po wszystkim powinno być `height: 1`):

```powershell
1..6 | % { curl.exe -s "http://localhost:800$_/chain/status" }
```

---

## 3) Start API lokalnie (bez Dockera)
Backend lokalnie (np. do debugowania):

```powershell
cd VetClinic\API
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

uvicorn vetclinic_api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 4) ReDoc / Swagger (API docs)
FastAPI daje dokumentację „z automatu”:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Docker (porty 8001..8006), to analogicznie:
- http://localhost:8001/docs oraz http://localhost:8001/redoc (dla node1)
- itd. dla node2..node6

---

## 5) Start GUI (lokalnie)

### Opcja A: uruchomienie jako moduł (jeśli GUI jest pakietem)
```powershell
cd VetClinic\GUI
python -m VetClinic.GUI.main
```

### Opcja B: uruchomienie pliku (jeśli jest `main.py` / `app.py`)
```powershell
cd VetClinic\GUI
python main.py
```

---

## 6) Start Grafany/Prometheusa (gdy są w Docker Compose)

```powershell
docker compose restart prometheus grafana
```

Logi :

```powershell
docker compose logs -f prometheus
docker compose logs -f grafana
```

---

## 8) Najszybsza kontrola metryk
Czy metryki żyją:

```powershell
curl.exe http://localhost:8001/metrics | findstr blockchain_
curl.exe http://localhost:8001/metrics | findstr tx_submitted_total
```

W Prometheus UI (Query):
- `up` (powinno być 6 serii)
- `blockchain_chain_height`
- `blockchain_mempool_size`
- `tx_submitted_total`

Uwaga: jak nie ma ruchu, to część metryk będzie pusta/zerowa. To nie „bug”, to brak bodźców.
