.PHONY: help
help:
	@echo "Dostępne cele:"
	@echo "  make cluster-up        - build + uruchomienie klastra 6 węzłów"
	@echo "  make cluster-down      - zatrzymanie klastra"
	@echo "  make test              - uruchomienie testów (pytest)"
	@echo "  make lint              - ruff + mypy + bandit (jeśli skonfigurowane)"
	@echo "  make scenario-healthy  - scenariusz: wszyscy zdrowi"
	@echo "  make scenario-faults1  - scenariusz: offline + slow"
	@echo "  make scenario-faults2  - scenariusz: 2 byzantine"
	@echo "  make scenario-faults3  - scenariusz: 3 byzantine (oczekiwany brak konsensusu)"


.PHONY: cluster-up
cluster-up:
	docker compose up --build

.PHONY: cluster-down
cluster-down:
	docker compose down

.PHONY: test
test:
	pytest

.PHONY: lint
lint:
	ruff vetclinic_api || true
	mypy vetclinic_api || true
	bandit -r vetclinic_api || true


.PHONY: scenario-healthy
scenario-healthy:
	python -m scripts.cluster_scenarios healthy

.PHONY: scenario-faults1
scenario-faults1:
	python -m scripts.cluster_scenarios faults_offline_slow

.PHONY: scenario-faults2
scenario-faults2:
	python -m scripts.cluster_scenarios faults_byzantine_2

.PHONY: scenario-faults3
scenario-faults3:
	python -m scripts.cluster_scenarios faults_byzantine_3
