# FreightHero Watchtower - Terraform Makefile
# Convenience commands for managing infrastructure

TF ?= terraform
ENV ?= dev
TF_DIR = infra/terraform/environments/$(ENV)

.PHONY: init plan apply destroy fmt validate lint clean

# Initialize Terraform
init:
	cd $(TF_DIR) && $(TF) init

# Plan changes
plan:
	cd $(TF_DIR) && $(TF) plan -out=tfplan

# Apply changes
apply:
	cd $(TF_DIR) && $(TF) apply tfplan

# Apply with auto-approve (use with caution!)
apply-auto:
	cd $(TF_DIR) && $(TF) apply -auto-approve

# Destroy infrastructure
destroy:
	cd $(TF_DIR) && $(TF) destroy

# Format Terraform files
fmt:
	$(TF) fmt -recursive infra/terraform/

# Validate Terraform files
validate:
	cd $(TF_DIR) && $(TF) validate

# Run fmt check (CI)
fmt-check:
	$(TF) fmt -check -recursive infra/terraform/

# Clean up plan files
clean:
	find infra/terraform -name "tfplan" -delete
	find infra/terraform -name ".terraform" -type d -exec rm -rf {} + 2>/dev/null || true
	find infra/terraform -name "terraform.tfstate*" -delete 2>/dev/null || true

# Show outputs
outputs:
	cd $(TF_DIR) && $(TF) output

# Show current state
state-list:
	cd $(TF_DIR) && $(TF) state list

# Import a resource
import:
	cd $(TF_DIR) && $(TF) import $(RESOURCE) $(ID)

# Taint a resource (force recreation)
taint:
	cd $(TF_DIR) && $(TF) taint $(RESOURCE)

# Refresh state
refresh:
	cd $(TF_DIR) && $(TF) refresh