resource "aws_cognito_user_pool" "pool" {
  name = "repomind-user-pool-${var.environment}"

  alias_attributes         = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_LINK"
    email_message_by_link = "Welcome to RepoMind! Click the link below to confirm your email: {##Click Here##}"
    email_subject_by_link = "Verify your RepoMind account"
  }

  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "email"
    required                 = true

    string_attribute_constraints {
      min_length = 5
      max_length = 100
    }
  }

  tags = {
    Name        = "repomind-cognito-pool-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name         = "repomind-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.pool.id

  generate_secret     = false
  explicit_auth_flows = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_USER_SRP_AUTH"]

  supported_identity_providers = ["COGNITO"]
  allowed_oauth_flows          = ["code", "implicit"]
  allowed_oauth_scopes         = ["phone", "email", "openid", "profile", "aws.cognito.signin.user.admin"]
  callback_urls                = ["http://localhost:3000", "https://repomind.io"]
  logout_urls                  = ["http://localhost:3000", "https://repomind.io"]
  allowed_oauth_flows_user_pool_client = true
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "repomind-auth-${var.environment}"
  user_pool_id = aws_cognito_user_pool.pool.id
}
