variable "aws_region" {
  type        = string
  description = "The target AWS region for deployment"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment name (e.g. production, staging)"
  default     = "production"
}

variable "db_password" {
  type        = string
  description = "The password for the RDS database administrator"
  sensitive   = true
  default     = "RepoMindSecurePass2026!"
}
