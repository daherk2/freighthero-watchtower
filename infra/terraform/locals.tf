# FreightHero Watchtower - Local Values

locals {
  project_name = "freighthero-watchtower"
  name_prefix  = "fh-${var.environment}"

  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}