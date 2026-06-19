variable "environment" {
  type        = string
  description = "Deployment environment name"
}

variable "db_password" {
  type        = string
  description = "The database password to store in Secrets Manager"
  sensitive   = true
}
