# FreightHero Watchtower - Dev Environment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "freighthero-terraform-state"
    key            = "watchtower/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "freighthero-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "FreightHero-Watchtower"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

provider "random" {}

module "vpc" {
  source = "../../modules/vpc"

  environment  = "dev"
  vpc_cidr     = "10.0.0.0/16"
  az_count     = 2
  project_name = "freighthero-watchtower"
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "ecr" {
  source = "../../modules/ecr"

  environment  = "dev"
  project_name = "freighthero-watchtower"
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "alb" {
  source = "../../modules/alb"

  environment    = "dev"
  project_name   = "freighthero-watchtower"
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnet_ids
  domain_name    = "dev-watchtower.freighthero.com"
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "rds" {
  source = "../../modules/rds"

  environment            = "dev"
  project_name           = "freighthero-watchtower"
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  db_password            = var.db_password
  db_instance_class      = "db.t3.micro"
  ecs_security_group_id  = module.ecs.security_group_id
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "redis" {
  source = "../../modules/elasticache"

  environment            = "dev"
  project_name           = "freighthero-watchtower"
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  ecs_security_group_id  = module.ecs.security_group_id
  redis_node_type        = "cache.t3.micro"
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "ecs" {
  source = "../../modules/ecs"

  environment          = "dev"
  project_name         = "freighthero-watchtower"
  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnet_ids
  public_subnet_ids    = module.vpc.public_subnet_ids
  alb_target_group_arn = module.alb.target_group_arn
  alb_dns_name         = module.alb.alb_dns_name
  alb_zone_id          = module.alb.alb_zone_id
  ecr_repository_url   = module.ecr.repository_url
  db_host              = module.rds.endpoint
  db_password          = var.db_password
  redis_host           = module.redis.primary_endpoint
  api_cpu              = 256
  api_memory           = 512
  api_desired_count    = 1
  celery_cpu           = 256
  celery_memory        = 512
  celery_desired_count = 1
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "cloudwatch" {
  source = "../../modules/cloudwatch"

  environment  = "dev"
  project_name = "freighthero-watchtower"
  ecs_cluster  = module.ecs.cluster_name
  alarm_email  = var.alarm_email
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "iam" {
  source = "../../modules/iam"

  environment       = "dev"
  project_name      = "freighthero-watchtower"
  ecs_task_role_arn = module.ecs.task_execution_role_arn
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

module "ssm" {
  source = "../../modules/ssm"

  environment    = "dev"
  project_name   = "freighthero-watchtower"
  db_endpoint    = module.rds.endpoint
  redis_endpoint = module.redis.primary_endpoint
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# ---------------------------------------------------------------
# Variables
# ---------------------------------------------------------------
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_password" {
  description = "RDS PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "alarm_email" {
  description = "Email for alarm notifications"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "rds_endpoint" {
  value = module.rds.endpoint
}

output "redis_endpoint" {
  value = module.redis.primary_endpoint
}

output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "api_url" {
  value = "https://dev-watchtower.freighthero.com"
}