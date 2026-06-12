# CloudWatch Module - Outputs

output "log_group_api" {
  description = "CloudWatch log group name for API"
  value       = aws_cloudwatch_log_group.api.name
}

output "log_group_celery_worker" {
  description = "CloudWatch log group name for Celery worker"
  value       = aws_cloudwatch_log_group.celery_worker.name
}

output "log_group_celery_beat" {
  description = "CloudWatch log group name for Celery beat"
  value       = aws_cloudwatch_log_group.celery_beat.name
}

output "alarm_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  value       = aws_sns_topic.alarms.arn
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}