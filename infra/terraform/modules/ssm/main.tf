# SSM Module - Main

# ---------------------------------------------------------------
# SSM Parameters for application configuration
# ---------------------------------------------------------------
resource "aws_ssm_parameter" "db_endpoint" {
  name        = "/${var.project_name}/${var.environment}/database/endpoint"
  description = "RDS PostgreSQL endpoint"
  type        = "String"
  value       = var.db_endpoint

  tags = var.common_tags
}

resource "aws_ssm_parameter" "redis_endpoint" {
  name        = "/${var.project_name}/${var.environment}/redis/endpoint"
  description = "ElastiCache Redis primary endpoint"
  type        = "String"
  value       = var.redis_endpoint

  tags = var.common_tags
}

resource "aws_ssm_parameter" "environment" {
  name        = "/${var.project_name}/${var.environment}/app/environment"
  description = "Application environment"
  type        = "String"
  value       = var.environment

  tags = var.common_tags
}

resource "aws_ssm_parameter" "app_name" {
  name        = "/${var.project_name}/${var.environment}/app/name"
  description = "Application name"
  type        = "String"
  value       = var.project_name

  tags = var.common_tags
}