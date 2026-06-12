# SSM Module - Outputs

output "db_endpoint_param" {
  description = "SSM parameter name for DB endpoint"
  value       = aws_ssm_parameter.db_endpoint.name
}

output "redis_endpoint_param" {
  description = "SSM parameter name for Redis endpoint"
  value       = aws_ssm_parameter.redis_endpoint.name
}