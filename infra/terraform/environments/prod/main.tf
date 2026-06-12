# FreightHero Watchtower - Production Environment

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
    key            = "watchtower/prod/terraform.tfstate"
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
      Environment = "prod"
      ManagedBy   = "terraform"
    }
  }
}

provider "random" {}

module "vpc" {
  source = "../../modules/vpc"

  environment  = "prod"
  vpc_cidr     = "10.2.0.0/16"
  az_count     = 3
  project_name = "freighthero-watchtower"
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

module "ecr" {
  source = "../../modules/ecr"

  environment  = "prod"
  project_name = "freighthero-watchtower"
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

module "alb" {
  source = "../../modules/alb"

  environment    = "prod"
  project_name   = "freighthero-watchtower"
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnet_ids
  domain_name    = "watchtower.freighthero.com"
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

module "rds" {
  source = "../../modules/rds"

  environment            = "prod"
  project_name           = "freighthero-watchtower"
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  db_password            = var.db_password
  db_instance_class      = "db.t3.medium"
  ecs_security_group_id  = module.ecs.security_group_id
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

module "redis" {
  source = "../../modules/elasticache"

  environment            = "prod"
  project_name           = "freighthero-watchtower"
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  ecs_security_group_id  = module.ecs.security_group_id
  redis_node_type        = "cache.t3.small"
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

module "ecs" {
  source = "../../modules/ecs"

  environment          = "prod"
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
  api_cpu              = 1024
  api_memory           = 2048
  api_desired_count    = 3
  celery_cpu           = 512
  celery_memory        = 1024
  celery_desired_count = 2
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

module "cloudwatch" {
  source = "../../modules/cloudwatch"

  environment  = "prod"
  project_name = "freighthero-watchtower"
  ecs_cluster  = module.ecs.cluster_name
  alarm_email  = var.alarm_email
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

module "iam" {
  source = "../../modules/iam"

  environment       = "prod"
  project_name      = "freighthero-watchtower"
  ecs_task_role_arn = module.ecs.task_execution_role_arn
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

module "ssm" {
  source = "../../modules/ssm"

  environment    = "prod"
  project_name   = "freighthero-watchtower"
  db_endpoint    = module.rds.endpoint
  redis_endpoint = module.redis.primary_endpoint
  common_tags = {
    Project     = "FreightHero-Watchtower"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

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
  value = "https://watchtower.freighthero.com"
}