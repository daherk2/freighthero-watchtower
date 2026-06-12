# SSM Module - Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "db_endpoint" {
  description = "RDS PostgreSQL endpoint"
  type        = string
}

variable "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}