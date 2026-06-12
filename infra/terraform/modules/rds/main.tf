# RDS Module - Main

# ---------------------------------------------------------------
# DB Subnet Group
# ---------------------------------------------------------------
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-db-subnet"
  })
}

# ---------------------------------------------------------------
# Security Group
# ---------------------------------------------------------------
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds"
  description = "RDS PostgreSQL security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
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
    Name = "${var.project_name}-${var.environment}-rds-sg"
  })
}

# ---------------------------------------------------------------
# RDS Parameter Group (PGVector support)
# ---------------------------------------------------------------
resource "aws_db_parameter_group" "pgvector" {
  name        = "${var.project_name}-${var.environment}-pgvector"
  family      = "postgres16"
  description = "PostgreSQL 16 parameter group with PGVector support"

  parameter {
    name  = "shared_preload_libraries"
    value = "pgvector"
  }
}

# ---------------------------------------------------------------
# RDS Instance
# ---------------------------------------------------------------
resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-${var.environment}"
  engine         = "postgres"
  engine_version = "16"

  instance_class    = var.db_instance_class
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "freighthero"
  username = "freighthero"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  parameter_group_name = aws_db_parameter_group.pgvector.name

  backup_retention_period = var.environment == "prod" ? 7 : 1
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  skip_final_snapshot       = var.environment != "prod"
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final-snapshot"
  deletion_protection       = var.environment == "prod"

  performance_insights_enabled          = var.environment == "prod"
  performance_insights_retention_period = var.environment == "prod" ? 7 : 0

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-postgres"
  })
}