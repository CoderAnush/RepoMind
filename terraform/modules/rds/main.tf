resource "aws_db_instance" "postgres" {
  identifier             = "repomind-db-${var.environment}"
  allocated_storage      = 20
  max_allocated_storage  = 100
  engine                 = "postgres"
  engine_version         = "15.3"
  instance_class         = "db.t4g.micro"
  db_name                = "repomind"
  username               = "postgres"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot    = true

  tags = {
    Name        = "repomind-rds-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_db_subnet_group" "db" {
  name       = "repomind-db-subnets-${var.environment}"
  subnet_ids = var.private_subnet_ids
  tags = {
    Name = "repomind-db-subnet-group-${var.environment}"
  }
}

resource "aws_security_group" "db" {
  name        = "repomind-rds-sg-${var.environment}"
  description = "Access security group for RDS Postgres database"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_sg_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "repomind-db-security-group-${var.environment}"
    Environment = var.environment
  }
}
