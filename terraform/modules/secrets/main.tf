resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "repomind-app-secrets-${var.environment}"
  recovery_window_in_days = 7
  tags = {
    Name        = "repomind-app-secrets-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets_version" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    POSTGRES_PASSWORD  = var.db_password
    SECRET_KEY         = "ENTERPRISE_SUPER_SECURE_TOKEN_GENERATION_KEY_FOR_JWT_SIGNATURES"
    OPENAI_API_KEY     = "PLACEHOLDER_OPENAI_KEY_TO_BE_UPDATED"
    ANTHROPIC_API_KEY   = "PLACEHOLDER_ANTHROPIC_KEY_TO_BE_UPDATED"
    QDRANT_API_KEY     = "PLACEHOLDER_QDRANT_KEY_TO_BE_UPDATED"
  })
}
