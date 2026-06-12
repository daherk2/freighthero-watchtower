# FreightHero Watchtower - Variables

# ---------------------------------------------------------------
# General
# ---------------------------------------------------------------
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# ---------------------------------------------------------------
# VPC
# ---------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of Availability Zones to use"
  type        = number
  default     = 2
}

# ---------------------------------------------------------------
# RDS
# ---------------------------------------------------------------
variable "db_password" {
  description = "RDS PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

# ---------------------------------------------------------------
# ElastiCache
# ---------------------------------------------------------------
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

# ---------------------------------------------------------------
# ECS - API
# ---------------------------------------------------------------
variable "api_cpu" {
  description = "API task CPU units (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "API task memory in MiB"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired number of API task instances"
  type        = number
  default     = 1
}

# ---------------------------------------------------------------
# ECS - Celery
# ---------------------------------------------------------------
variable "celery_cpu" {
  description = "Celery worker task CPU units"
  type        = number
  default     = 256
}

variable "celery_memory" {
  description = "Celery worker task memory in MiB"
  type        = number
  default     = 512
}

variable "celery_desired_count" {
  description = "Desired number of Celery worker instances"
  type        = number
  default     = 1
}

# ---------------------------------------------------------------
# Domain / SSL
# ---------------------------------------------------------------
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "watchtower.freighthero.com"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}