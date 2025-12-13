# Etap 1: Implementacja metryk Prometheus (API)

Cel: mieć działające `GET /metrics` oraz podstawowe liczniki/histogramy z kontraktu.

## Zależności

- `prometheus-client`

Dodaj do `requirements.txt`:

- prometheus-client==0.21.0 (albo bez pinowania, jeśli już masz politykę inaczej)

## Pliki do dodania

### 1) vetclinic_api/metrics.py

- Definiuje Registry i metryki:
  - http_requests_total (Counter)
  - http_request_duration_seconds (Histogram)
  - http_exceptions_total (Counter)
  - + kilka kluczowych blockchainowych (minimum: chain_height, mempool_size, tx_submitted_total, consensus_votes_total)
- Dodaje endpoint FastAPI: `GET /metrics` (Response typu text/plain; version=0.0.4)

### 2) Middleware HTTP (np. w vetclinic_api/main.py lub osobny plik)

- Mierzy czas requestu.
- Normalizuje `path` (np. bez dynamicznych id: /animals/{id} zamiast /animals/123).
- Inkrementuje liczniki i histogramy.

## Integracja w main.py

- Import `from vetclinic_api.metrics import metrics_router, instrumentator_middleware`
- `app.include_router(metrics_router)`
- `app.middleware("http")(instrumentator_middleware)`

## Minimalny Definition of Done

- `GET /metrics` działa lokalnie i w docker-compose
- Po wejściu na kilka endpointów rosną:
  - http_requests_total
  - histogram duration ma obserwacje
- Po submit transakcji rośnie tx_submitted_total

## Co NIE robimy na Etapie 1

- Grafana dashboards (to Etap 2)
- Alerty (Etap 3)
- Metryki o bardzo dużej kardynalności (tx_id jako label = zło)

## Szybki test

1. uruchom API
2. uderz kilka razy w endpointy: /chain/status, /tx/submit
3. sprawdź:
   - curl http://localhost:8000/metrics
   - czy widać `http_requests_total` i `tx_submitted_total`
