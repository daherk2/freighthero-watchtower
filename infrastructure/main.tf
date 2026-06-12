# Terraform configuration for FreightHero Watchtower
# AWS infrastructure provisioning

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "freighthero-terraform-state"
    key    = "watchtower/terraform.tfstate"
    region = "us-east-1"
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

# --- VPC ---

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "freighthero-${var.environment}-vpc"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "freighthero-${var.environment}-private-${count.index + 1}"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                 = aws_vpc.main.id
  cidr_block             = "10.0.${count.index + 10}.0/24"
  availability_zone      = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "freighthero-${var.environment}-public-${count.index + 1}"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# --- ECS Cluster ---

resource "aws_ecs_cluster" "main" {
  name = "freighthero-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# --- RDS PostgreSQL with PGVector ---

resource "aws_db_subnet_group" "main" {
  name       = "freighthero-${var.environment}"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "freighthero-${var.environment}-db-subnet"
  }
}

resource "aws_security_group" "rds" {
  name        = "freighthero-${var.environment}-rds"
  description = "RDS PostgreSQL security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres" {
  identifier           = "freighthero-${var.environment}"
  engine               = "postgres"
  engine_version       = "16"
  instance_class       = var.db_instance_class
  allocated_storage    = 20
  storage_encrypted    = true
  username             = "freighthero"
  password             = var.db_password
  db_name              = "freighthero"
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot  = true

  tags = {
    Name = "freighthero-${var.environment}-postgres"
  }
}

# --- ElastiCache Redis ---

resource "aws_security_group" "redis" {
  name        = "freighthero-${var.environment}-redis"
  description = "Redis security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "freighthero-${var.environment}"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = "freighthero-${var.environment}"
  description                   = "FreightHero Redis cluster"
  node_type                     = var.redis_node_type
  number_cache_clusters         = 1
  subnet_group_name             = aws_elasticache_subnet_group.main.name
  security_group_ids            = [aws_security_group.redis.id]
  automatic_failover_enabled    = false
  engine                        = "redis"
  engine_version                = "7"
  parameter_group_name           = "default.redis7"
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
}

# --- ECS Service ---

resource "aws_security_group" "ecs" {
  name        = "freighthero-${var.environment}-ecs"
  description = "ECS service security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "freighthero-${var.environment}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${var.ecr_repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "DATABASE_URL", value = "postgresql+asyncpg://freighthero:${var.db_password}@${aws_db_instance.postgres.endpoint}/freighthero" },
        { name = "REDIS_URL", value = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0" },
        { name = "CELERY_BROKER_URL", value = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/1" },
        { name = "CELERY_RESULT_BACKEND", value = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/2" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/freighthero-${var.environment}"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
    }
  ])
}

# --- ALB ---

resource "aws_security_group" "alb" {
  name        = "freighthero-${var.environment}-alb"
  description = "ALB security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- Variables ---

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "db_password" {
  description = "RDS PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "api_cpu" {
  description = "API task CPU units"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "API task memory (MiB)"
  type        = number
  default     = 1024
}

variable "ecr_repository_url" {
  description = "ECR repository URL for the API image"
  type        = string
}

# --- Outputs ---

output "vpc_id" {
  value = aws_vpc.main.id
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}