terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source      = "./modules/vpc"
  environment = var.environment
}

module "secrets" {
  source      = "./modules/secrets"
  environment = var.environment
  db_password = var.db_password
}

module "cognito" {
  source      = "./modules/cognito"
  environment = var.environment
}

module "rds" {
  source             = "./modules/rds"
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_password        = var.db_password
  ecs_sg_id          = module.ecs.ecs_security_group_id
}

module "ecs" {
  source                  = "./modules/ecs"
  environment             = var.environment
  aws_region              = var.aws_region
  vpc_id                  = module.vpc.vpc_id
  public_subnet_ids       = module.vpc.public_subnet_ids
  private_subnet_ids      = module.vpc.private_subnet_ids
  db_address              = module.rds.db_address
  db_name                 = module.rds.db_name
  db_user                 = module.rds.db_user
  secrets_manager_arn     = module.secrets.secret_arn
  cognito_user_pool_id    = module.cognito.user_pool_id
  cognito_app_client_id  = module.cognito.user_pool_client_id
}

module "s3_cloudfront" {
  source      = "./modules/s3_cloudfront"
  environment = var.environment
}
