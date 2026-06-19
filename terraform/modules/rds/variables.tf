variable "environment" {
  type        = string
  description = "Deployment environment name"
}

variable "vpc_id" {
  type        = string
  description = "The ID of the VPC"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "The list of private subnets for RDS placement"
}

variable "db_password" {
  type        = string
  description = "RDS master password"
  sensitive   = true
}

variable "ecs_sg_id" {
  type        = string
  description = "The security group ID of the ECS Fargate tasks to allow DB connections"
}
