# ECS Module - Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ECS service"
  type        = list(string)
}

variable "alb_target_group_arn" {
  description = "ALB target group ARN for the API"
  type        = string
}

variable "alb_listener_arn" {
  description = "ALB HTTPS listener ARN"
  type        = string
  default     = ""
}

variable "alb_dns_name" {
  description = "ALB DNS name"
  type        = string
}

variable "alb_zone_id" {
  description = "ALB Route53 zone ID"
  type        = string
}

variable "ecr_repository_url" {
  description = "ECR repository URL for the API image"
  type        = string
}

variable "db_host" {
  description = "RDS PostgreSQL endpoint"
  type        = string
}

variable "db_password" {
  description = "RDS PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "redis_host" {
  description = "ElastiCache Redis primary endpoint"
  type        = string
}

variable "api_cpu" {
  description = "API task CPU units"
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

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}