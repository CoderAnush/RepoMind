output "ecs_security_group_id" {
  value       = aws_security_group.ecs.id
  description = "The security group ID of the ECS Fargate tasks"
}

output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "The DNS name of the backend Application Load Balancer"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "The ECR repository URL to push backend Docker images to"
}
