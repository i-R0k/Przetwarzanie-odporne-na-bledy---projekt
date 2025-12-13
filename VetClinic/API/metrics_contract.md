# Metrics Contract (VetClinic API)

Ten dokument definiuje kontrakt metryk eksportowanych przez API w formacie Prometheus.
Celem jest obserwowalność: stan sieci (6 węzłów), głosowania, transakcje, bloki, błędy i opóźnienia.

## Standard

- Ekspozycja: `GET /metrics`
- Format: Prometheus text exposition format
- Etykiety: ograniczamy kardynalność (nie wrzucamy tx_id, user_id, payload itp. jako label)

---

## Metryki HTTP (API)

### http_requests_total

- Typ: Counter
- Etykiety: `method`, `path`, `status`
- Opis: Liczba obsłużonych żądań HTTP przez API.

Aktualizacja:

- Middleware HTTP (globalnie dla FastAPI).

### http_request_duration_seconds

- Typ: Histogram
- Etykiety: `method`, `path`
- Opis: Czas obsługi żądań HTTP.

Aktualizacja:

- Middleware HTTP (globalnie dla FastAPI).

### http_exceptions_total

- Typ: Counter
- Etykiety: `exception_type`, `path`
- Opis: Liczba wyjątków rzuconych w trakcie obsługi requestów (zanim zamienią się w odpowiedź HTTP).

Aktualizacja:

- Middleware / global exception handler (FastAPI).

---

## Blockchain / Konsensus / Sieć 6 serwerów

### blockchain_chain_height

- Typ: Gauge
- Etykiety: `node`
- Opis: Aktualna wysokość łańcucha na danym węźle.

Aktualizacja:

- `GET /chain/status` oraz/lub wewnętrzna funkcja odczytu storage (np. `storage.get_chain()`).

### blockchain_mempool_size

- Typ: Gauge
- Etykiety: `node`
- Opis: Liczba transakcji w mempoolu danego węzła.

Aktualizacja:

- `GET /chain/status` oraz/lub funkcja mempool.

### tx_submitted_total

- Typ: Counter
- Etykiety: `node`
- Opis: Liczba transakcji przyjętych do rozpatrzenia (submit) przez dany węzeł.

Aktualizacja:

- Endpoint `POST /tx/submit` (router blockchain/transakcji).

### tx_rejected_total

- Typ: Counter
- Etykiety: `node`, `reason`
- Opis: Liczba odrzuconych transakcji (np. walidacja, brak kworum, timeout).

Aktualizacja:

- Endpoint `POST /tx/submit` oraz logika walidacji/konsensusu.

### consensus_votes_total

- Typ: Counter
- Etykiety: `node`, `vote` (`yes|no|timeout|error`)
- Opis: Liczba oddanych głosów przez węzeł w procesie zatwierdzania transakcji/bloku.

Aktualizacja:

- Funkcja realizująca głosowanie (np. `vote_on_tx(...)` / `broadcast_vote(...)`).

### consensus_rounds_total

- Typ: Counter
- Etykiety: `result` (`committed|rejected|timeout`)
- Opis: Liczba rund konsensusu zakończonych wynikiem commit/reject/timeout.

Aktualizacja:

- Koordynator konsensusu (tam gdzie liczysz głosy i podejmujesz decyzję).

### blocks_mined_total

- Typ: Counter
- Etykiety: `node`
- Opis: Liczba bloków utworzonych (leader/miner) przez dany węzeł.

Aktualizacja:

- Funkcja tworząca blok (np. `mine_block()` / `create_block()`).

### blocks_committed_total

- Typ: Counter
- Etykiety: `node`
- Opis: Liczba bloków dołączonych do łańcucha (zaakceptowanych) na węźle.

Aktualizacja:

- Miejsce, gdzie finalnie zapisujesz blok do storage.

### chain_verify_total

- Typ: Counter
- Etykiety: `node`, `result` (`ok|invalid`)
- Opis: Liczba wykonań weryfikacji integralności łańcucha.

Aktualizacja:

- Endpoint `GET /chain/verify`.

### chain_verify_duration_seconds

- Typ: Histogram
- Etykiety: `node`
- Opis: Czas wykonywania weryfikacji łańcucha.

Aktualizacja:

- Endpoint `GET /chain/verify`.

---

## Symulacje błędów (Fault Injection)

Zakładamy, że mamy 6 węzłów i możliwość wyboru, który “psujemy” (panel admina lub endpointy administracyjne).
Metryki mają pokazać, że system dalej działa / degraduje się zgodnie z oczekiwaniem.

### faults_enabled

- Typ: Gauge
- Etykiety: `node`, `fault_type`
- Opis: Czy dany fault jest aktualnie aktywny na danym węźle (0/1).

Aktualizacja:

- Endpointy administracyjne typu `POST /admin/faults/enable` i `POST /admin/faults/disable`
  albo bezpośrednie przełączenie w konfiguracji runtime.

### faults_events_total

- Typ: Counter
- Etykiety: `node`, `fault_type`
- Opis: Ile razy fault faktycznie “uderzył” (np. opóźnił request, zrzucił odpowiedź, dał złą odpowiedź).

Aktualizacja:

- W miejscu implementacji fault injection (wrapper klienta HTTP / handler żądań / warstwa konsensusu).

### faults_dropped_requests_total

- Typ: Counter
- Etykiety: `node`, `fault_type`
- Opis: Ile requestów/wiadomości zostało celowo “zgubionych” przez fault.

Aktualizacja:

- Warstwa komunikacji między węzłami.

### faults_corrupted_responses_total

- Typ: Counter
- Etykiety: `node`, `fault_type`
- Opis: Ile razy zasymulowano odpowiedź z uszkodzonym payloadem/danymi.

Aktualizacja:

- Warstwa komunikacji / zwrot odpowiedzi węzła.

### node_up

- Typ: Gauge
- Etykiety: `node`
- Opis: Czy węzeł jest “osiągalny” wg monitoringu (1=ok, 0=down). To logiczny stan, nie docker.

Aktualizacja:

- Healthcheck (np. `GET /health`) lub ping z koordynatora; ustawiane per cykl.

---

## Konwencje nazw `node`

- `node` to stała nazwa: `node1..node6` (nie port, nie host).
- Porty i hosty nie jako label (kardynalność i chaos).
