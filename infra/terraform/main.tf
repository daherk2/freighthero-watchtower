# FreightHero Watchtower - Terraform Root Module
# AWS infrastructure provisioning

# ---------------------------------------------------------------
# Remote State
# ---------------------------------------------------------------
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
    key            = "watchtower/terraform.tfstate"
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
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "random" {}

# ---------------------------------------------------------------
# Data Sources
# ---------------------------------------------------------------
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ---------------------------------------------------------------
# VPC Module
# ---------------------------------------------------------------
module "vpc" {
  source = "./modules/vpc"

  environment     = var.environment
  vpc_cidr        = var.vpc_cidr
  az_count        = var.az_count
  project_name    = local.project_name
  common_tags     = local.common_tags
}

# ---------------------------------------------------------------
# ECR Module
# ---------------------------------------------------------------
module "ecr" {
  source = "./modules/ecr"

  environment  = var.environment
  project_name = local.project_name
  common_tags  = local.common_tags
}

# ---------------------------------------------------------------
# ALB Module
# ---------------------------------------------------------------
module "alb" {
  source = "./modules/alb"

  environment    = var.environment
  project_name   = local.project_name
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnet_ids
  common_tags    = local.common_tags
}

# ---------------------------------------------------------------
# RDS Module
# ---------------------------------------------------------------
module "rds" {
  source = "./modules/rds"

  environment       = var.environment
  project_name      = local.project_name
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_password       = var.db_password
  db_instance_class = var.db_instance_class
  ecs_security_group_id = module.ecs.security_group_id
  common_tags       = local.common_tags
}

# ---------------------------------------------------------------
# ElastiCache (Redis) Module
# ---------------------------------------------------------------
module "redis" {
  source = "./modules/elasticache"

  environment       = var.environment
  project_name      = local.project_name
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  ecs_security_group_id = module.ecs.security_group_id
  redis_node_type   = var.redis_node_type
  common_tags       = local.common_tags
}

# ---------------------------------------------------------------
# ECS Module
# ---------------------------------------------------------------
module "ecs" {
  source = "./modules/ecs"

  environment          = var.environment
  project_name         = local.project_name
  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnet_ids
  public_subnet_ids    = module.vpc.public_subnet_ids
  alb_target_group_arn = module.alb.target_group_arn
  alb_listener_arn     = module.alb.https_listener_arn
  alb_dns_name         = module.alb.alb_dns_name
  alb_zone_id          = module.alb.alb_zone_id
  ecr_repository_url   = module.ecr.repository_url
  db_host              = module.rds.endpoint
  db_password          = var.db_password
  redis_host           = module.redis.primary_endpoint
  api_cpu              = var.api_cpu
  api_memory           = var.api_memory
  celery_cpu           = var.celery_cpu
  celery_memory        = var.celery_memory
  common_tags          = local.common_tags
}

# ---------------------------------------------------------------
# CloudWatch Module
# ---------------------------------------------------------------
module "cloudwatch" {
  source = "./modules/cloudwatch"

  environment    = var.environment
  project_name   = local.project_name
  ecs_cluster    = module.ecs.cluster_name
  common_tags    = local.common_tags
}

# ---------------------------------------------------------------
# IAM Module
# ---------------------------------------------------------------
module "iam" {
  source = "./modules/iam"

  environment    = var.environment
  project_name   = local.project_name
  ecs_task_role_arn = module.ecs.task_execution_role_arn
  common_tags    = local.common_tags
}

# ---------------------------------------------------------------
# SSM Parameter Store
# ---------------------------------------------------------------
module "ssm" {
  source = "./modules/ssm"

  environment    = var.environment
  project_name   = local.project_name
  db_endpoint    = module.rds.endpoint
  redis_endpoint = module.redis.primary_endpoint
  common_tags    = local.common_tags
}