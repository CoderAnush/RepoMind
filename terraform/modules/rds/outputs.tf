output "db_address" {
  value       = aws_db_instance.postgres.address
  description = "The address of the RDS database"
}

output "db_name" {
  value       = aws_db_instance.postgres.db_name
  description = "The name of the database"
}

output "db_user" {
  value       = aws_db_instance.postgres.username
  description = "The username for the database"
}
