# ElastiCache Module - Main

# ---------------------------------------------------------------
# Security Group
# ---------------------------------------------------------------
resource "aws_security_group" "redis" {
  name        = "${var.project_name}-${var.environment}-redis"
  description = "Redis security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-redis-sg"
  })
}

# ---------------------------------------------------------------
# Subnet Group
# ---------------------------------------------------------------
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-redis-subnet"
  })
}

# ---------------------------------------------------------------
# Parameter Group
# ---------------------------------------------------------------
resource "aws_elasticache_parameter_group" "redis" {
  name        = "${var.project_name}-${var.environment}"
  family      = "redis7"
  description = "Redis 7 parameter group for ${var.environment}"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}

# ---------------------------------------------------------------
# Replication Group (Redis)
# ---------------------------------------------------------------
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = "${var.project_name}-${var.environment}"
  description                   = "FreightHero Redis cluster for ${var.environment}"
  node_type                     = var.redis_node_type
  number_cache_clusters         = var.environment == "prod" ? 2 : 1
  subnet_group_name              = aws_elasticache_subnet_group.main.name
  security_group_ids             = [aws_security_group.redis.id]
  parameter_group_name           = aws_elasticache_parameter_group.redis.name
  automatic_failover_enabled     = var.environment == "prod"
  engine                        = "redis"
  engine_version                = "7"
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true

  snapshot_retention_limit = var.environment == "prod" ? 5 : 1
  snapshot_window         = "03:00-05:00"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-redis"
  })
}