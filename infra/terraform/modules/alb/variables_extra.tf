# ALB Module - Additional Variables

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "watchtower.freighthero.com"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS. Leave empty to create one."
  type        = string
  default     = ""
}