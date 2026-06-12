# CloudWatch Module - Main

# ---------------------------------------------------------------
# Log Groups
# ---------------------------------------------------------------
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}-${var.environment}/api"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-api-logs"
  })
}

resource "aws_cloudwatch_log_group" "celery_worker" {
  name              = "/ecs/${var.project_name}-${var.environment}/celery-worker"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-celery-worker-logs"
  })
}

resource "aws_cloudwatch_log_group" "celery_beat" {
  name              = "/ecs/${var.project_name}-${var.environment}/celery-beat"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-celery-beat-logs"
  })
}

# ---------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "ECS CPU Utilization"
          region  = data.aws_region.current.name
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.project_name}-${var.environment}-api", "ClusterName", var.ecs_cluster],
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.project_name}-${var.environment}-celery-worker", "ClusterName", var.ecs_cluster]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "ECS Memory Utilization"
          region  = data.aws_region.current.name
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "${var.project_name}-${var.environment}-api", "ClusterName", var.ecs_cluster],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "${var.project_name}-${var.environment}-celery-worker", "ClusterName", var.ecs_cluster]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "RDS Connections"
          region  = data.aws_region.current.name
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "${var.project_name}-${var.environment}"]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6
        properties = {
          title   = "ElastiCache Cache Hits"
          region  = data.aws_region.current.name
          metrics = [
            ["AWS/ElastiCache", "CacheHits", "CacheClusterId", "${var.project_name}-${var.environment}"],
            ["AWS/ElastiCache", "CacheMisses", "CacheClusterId", "${var.project_name}-${var.environment}"]
          ]
          period = 300
          stat   = "Average"
        }
      }
    ]
  })
}

data "aws_region" "current" {}

# ---------------------------------------------------------------
# Alarms
# ---------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "api_high_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-api-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "API CPU utilization above 80%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ServiceName = "${var.project_name}-${var.environment}-api"
    ClusterName = var.ecs_cluster
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_high_memory" {
  alarm_name          = "${var.project_name}-${var.environment}-api-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "API memory utilization above 85%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ServiceName = "${var.project_name}-${var.environment}-api"
    ClusterName = var.ecs_cluster
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_high_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization above 80%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = "${var.project_name}-${var.environment}"
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_low_storage" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5000000000  # 5 GB in bytes
  alarm_description   = "RDS free storage space below 5GB"
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = "${var.project_name}-${var.environment}"
  }

  tags = var.common_tags
}

# ---------------------------------------------------------------
# SNS Topic for Alarms
# ---------------------------------------------------------------
resource "aws_sns_topic" "alarms" {
  name = "${var.project_name}-${var.environment}-alarms"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-alarm-topic"
  })
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

resource "aws_cloudwatch_metric_alarm" "api_health_check" {
  alarm_name          = "${var.project_name}-${var.environment}-api-health-check"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "API health check failing - no healthy hosts"
  treat_missing_data  = "breaching"

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = var.common_tags
}

variable "alarm_email" {
  description = "Email address for alarm notifications"
  type        = string
  default     = ""
}