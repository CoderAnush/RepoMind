variable "environment" {
  type        = string
  description = "Deployment environment name"
}

variable "vpc_cidr" {
  type        = string
  description = "The IP address range for the VPC"
  default     = "10.0.0.0/16"
}
