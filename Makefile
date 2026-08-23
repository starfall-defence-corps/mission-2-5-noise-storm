SHELL := /bin/bash
ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: doctor submit setup test reset destroy ssh-app ssh-web ssh-db help

help: ## Show available commands
	@echo ""
	@echo "=============================================="
	@echo "  STARFALL DEFENCE CORPS ACADEMY"
	@echo "  Mission 2.5: Noise Storm"
	@echo "=============================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

doctor: ## Check your machine is mission-ready (Docker, ports, tools)
	@bash $(ROOT_DIR)/scripts/doctor.sh

setup: ## Start the fleet + range (3 target nodes, under attack)
	@bash $(ROOT_DIR)/scripts/setup-lab.sh

test: ## Ask ARIA to verify your work
	@bash $(ROOT_DIR)/scripts/check-work.sh

submit: ## Submit your work for ARIA review (branch, commit, push, PR)
	@bash $(ROOT_DIR)/scripts/submit.sh

reset: ## Destroy and rebuild the fleet + re-arm the storm
	@bash $(ROOT_DIR)/scripts/reset-lab.sh

destroy: ## Tear down everything (containers, keys, venv, range state)
	@bash $(ROOT_DIR)/scripts/destroy-lab.sh

ssh-app: ## SSH into sdc-app (fleet application node)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null cadet@localhost -p 2221

ssh-web: ## SSH into sdc-web (fleet web server)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null cadet@localhost -p 2222

ssh-db: ## SSH into sdc-db (fleet database server)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null cadet@localhost -p 2223
