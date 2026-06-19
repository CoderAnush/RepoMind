variable "environment" {
  type        = string
  description = "Deployment environment name"
}

variable "aws_region" {
  type        = string
  description = "The target AWS region"
}

variable "vpc_id" {
  type        = string
  description = "The ID of the VPC"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "The list of public subnets for the ALB"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "The list of private subnets for ECS tasks"
}

variable "db_address" {
  type        = string
  description = "PostgreSQL DB connection address"
}

variable "db_name" {
  type        = string
  description = "Database name"
}

variable "db_user" {
  type        = string
  description = "Database username"
}

variable "secrets_manager_arn" {
  type        = string
  description = "The ARN of Secrets Manager"
}

variable "cognito_user_pool_id" {
  type        = string
  description = "Cognito User Pool ID"
}

variable "cognito_app_client_id" {
  type        = string
  description = "Cognito App Client ID"
}
