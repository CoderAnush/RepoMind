output "secret_arn" {
  value       = aws_secretsmanager_secret.app_secrets.arn
  description = "The ARN of the Secrets Manager secret"
}
