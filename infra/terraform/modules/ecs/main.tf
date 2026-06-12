# ECS Module - Main

# ---------------------------------------------------------------
# ECS Cluster
# ---------------------------------------------------------------
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs_exec.name
      }
    }
  }
}

resource "aws_cloudwatch_log_group" "ecs_exec" {
  name              = "/ecs/${var.project_name}-${var.environment}/exec"
  retention_in_days = 30
}

# ---------------------------------------------------------------
# Security Group - ECS Tasks
# ---------------------------------------------------------------
resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-${var.environment}-ecs"
  description = "ECS tasks security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = []  # ALB SG added dynamically
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-ecs-sg"
  })
}

# ---------------------------------------------------------------
# CloudWatch Log Groups
# ---------------------------------------------------------------
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}-${var.environment}/api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "celery_worker" {
  name              = "/ecs/${var.project_name}-${var.environment}/celery-worker"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "celery_beat" {
  name              = "/ecs/${var.project_name}-${var.environment}/celery-beat"
  retention_in_days = 30
}

# ---------------------------------------------------------------
# IAM Roles - Task Execution
# ---------------------------------------------------------------
resource "aws_iam_role" "task_execution" {
  name = "${var.project_name}-${var.environment}-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_policy" "task_execution_extras" {
  name        = "${var.project_name}-${var.environment}-task-execution-extras"
  description = "Additional permissions for ECS task execution"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter",
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution_extras" {
  role       = aws_iam_role.task_execution.name
  policy_arn = aws_iam_policy.task_execution_extras.arn
}

# ---------------------------------------------------------------
# IAM Roles - Task Role (application permissions)
# ---------------------------------------------------------------
resource "aws_iam_role" "task_role" {
  name = "${var.project_name}-${var.environment}-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "task_role" {
  name        = "${var.project_name}-${var.environment}-task-policy"
  description = "Application-level permissions for ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:GetSamplingStatisticSummaries"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "task_role" {
  role       = aws_iam_role.task_role.name
  policy_arn = aws_iam_policy.task_role.arn
}

# ---------------------------------------------------------------
# Task Definitions
# ---------------------------------------------------------------
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-${var.environment}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn             = aws_iam_role.task_role.arn

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
        { name = "APP_NAME", value = "freighthero-watchtower" },
        { name = "ENVIRONMENT", value = var.environment },
        { name = "DATABASE_URL", value = "postgresql+asyncpg://freighthero:${var.db_password}@${var.db_host}/freighthero" },
        { name = "REDIS_URL", value = "redis://${var.redis_host}:6379/0" },
        { name = "CELERY_BROKER_URL", value = "redis://${var.redis_host}:6379/1" },
        { name = "CELERY_RESULT_BACKEND", value = "redis://${var.redis_host}:6379/2" },
        { name = "OTEL_EXPORTER_ENDPOINT", value = "http://localhost:4317" },
        { name = "OTEL_SERVICE_NAME", value = "freighthero-watchtower" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "api"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 10
      }
    }
  ])
}

resource "aws_ecs_task_definition" "celery_worker" {
  family                   = "${var.project_name}-${var.environment}-celery-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.celery_cpu
  memory                   = var.celery_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn             = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "celery-worker"
      image     = "${var.ecr_repository_url}:latest"
      essential = true
      command   = ["celery", "-A", "src.infrastructure.queue", "worker", "--loglevel=info", "-Q", "events,agent,timers,memory"]
      environment = [
        { name = "APP_NAME", value = "freighthero-watchtower" },
        { name = "ENVIRONMENT", value = var.environment },
        { name = "DATABASE_URL", value = "postgresql+asyncpg://freighthero:${var.db_password}@${var.db_host}/freighthero" },
        { name = "REDIS_URL", value = "redis://${var.redis_host}:6379/0" },
        { name = "CELERY_BROKER_URL", value = "redis://${var.redis_host}:6379/1" },
        { name = "CELERY_RESULT_BACKEND", value = "redis://${var.redis_host}:6379/2" },
        { name = "OTEL_EXPORTER_ENDPOINT", value = "http://localhost:4317" },
        { name = "OTEL_SERVICE_NAME", value = "freighthero-watchtower-celery" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.celery_worker.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "celery-worker"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "celery_beat" {
  family                   = "${var.project_name}-${var.environment}-celery-beat"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn             = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "celery-beat"
      image     = "${var.ecr_repository_url}:latest"
      essential = true
      command   = ["celery", "-A", "src.infrastructure.queue", "beat", "--loglevel=info"]
      environment = [
        { name = "APP_NAME", value = "freighthero-watchtower" },
        { name = "ENVIRONMENT", value = var.environment },
        { name = "DATABASE_URL", value = "postgresql+asyncpg://freighthero:${var.db_password}@${var.db_host}/freighthero" },
        { name = "REDIS_URL", value = "redis://${var.redis_host}:6379/0" },
        { name = "CELERY_BROKER_URL", value = "redis://${var.redis_host}:6379/1" },
        { name = "CELERY_RESULT_BACKEND", value = "redis://${var.redis_host}:6379/2" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.celery_beat.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "celery-beat"
        }
      }
    }
  ])
}

data "aws_region" "current" {}

# ---------------------------------------------------------------
# ECS Services
# ---------------------------------------------------------------
resource "aws_ecs_service" "api" {
  name                   = "${var.project_name}-${var.environment}-api"
  cluster                = aws_ecs_cluster.main.id
  task_definition        = aws_ecs_task_definition.api.arn
  desired_count          = var.api_desired_count
  launch_type            = "FARGATE"
  enable_execute_command = true

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.alb_target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_ecs_service" "celery_worker" {
  name                   = "${var.project_name}-${var.environment}-celery-worker"
  cluster                = aws_ecs_cluster.main.id
  task_definition        = aws_ecs_task_definition.celery_worker.arn
  desired_count          = var.celery_desired_count
  launch_type            = "FARGATE"
  enable_execute_command = true

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_ecs_service" "celery_beat" {
  name                   = "${var.project_name}-${var.environment}-celery-beat"
  cluster                = aws_ecs_cluster.main.id
  task_definition        = aws_ecs_task_definition.celery_beat.arn
  desired_count          = 1
  launch_type            = "FARGATE"
  enable_execute_command = true

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
}

# ---------------------------------------------------------------
# Auto Scaling
# ---------------------------------------------------------------
resource "aws_appautoscaling_target" "api" {
  max_capacity       = 10
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "${var.project_name}-${var.environment}-api-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70
    scale_out_cooldown = 60
    scale_in_cooldown  = 300
  }
}

resource "aws_appautoscaling_policy" "api_memory" {
  name               = "${var.project_name}-${var.environment}-api-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80
    scale_out_cooldown = 60
    scale_in_cooldown  = 300
  }
}