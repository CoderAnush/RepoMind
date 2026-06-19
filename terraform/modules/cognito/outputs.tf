output "user_pool_id" {
  value       = aws_cognito_user_pool.pool.id
  description = "The ID of the Cognito User Pool"
}

output "user_pool_client_id" {
  value       = aws_cognito_user_pool_client.client.id
  description = "The ID of the Cognito User Pool Client"
}

output "auth_domain" {
  value       = aws_cognito_user_pool_domain.main.domain
  description = "The auth sub-domain configured for Cognito login endpoints"
}
