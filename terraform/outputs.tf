output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "The ID of the generated VPC"
}

output "database_address" {
  value       = module.rds.db_address
  description = "Connection address of the RDS Postgres DB"
}

output "cognito_user_pool_id" {
  value       = module.cognito.user_pool_id
  description = "Cognito User Pool ID"
}

output "backend_alb_dns_name" {
  value       = module.ecs.alb_dns_name
  description = "DNS endpoint for backend service Application Load Balancer"
}

output "frontend_cloudfront_domain" {
  value       = module.s3_cloudfront.cloudfront_domain_name
  description = "CloudFront distribution domain name for the React SPA"
}
