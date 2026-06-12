# ElastiCache Module - Outputs

output "primary_endpoint" {
  description = "ElastiCache Redis primary endpoint address"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "replication_group_id" {
  description = "ElastiCache Redis replication group ID"
  value       = aws_elasticache_replication_group.redis.id
}

output "security_group_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}