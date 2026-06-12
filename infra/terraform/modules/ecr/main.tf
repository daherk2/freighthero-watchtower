# ECR Module - Main

# ---------------------------------------------------------------
# ECR Repository
# ---------------------------------------------------------------
resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}/${var.environment}"
  image_tag_mutability = var.environment == "prod" ? "IMMUTABLE" : "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-ecr"
  })
}

# ---------------------------------------------------------------
# Lifecycle Policy
# ---------------------------------------------------------------
resource "aws_ecr_lifecycle_policy" "api" {
  repository_name = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Remove untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}