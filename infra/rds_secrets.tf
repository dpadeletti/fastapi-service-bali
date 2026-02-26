resource "random_password" "db" {
  length  = 24
  special = false
}

resource "aws_db_subnet_group" "db" {
  name       = "${var.project_name}-${var.env}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
}

# RDS PostgreSQL 15+ supporta pgvector come estensione nativa
resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-${var.env}-db"
  engine                 = "postgres"
  engine_version         = "15.10"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  db_subnet_group_name   = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  # Abilita pgvector tramite parameter group
  parameter_group_name = aws_db_parameter_group.postgres.name

  publicly_accessible = false
  skip_final_snapshot = true
  deletion_protection = false
}

# Parameter group con pgvector abilitato
resource "aws_db_parameter_group" "postgres" {
  name   = "${var.project_name}-${var.env}-pg15"
  family = "postgres15"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${var.project_name}/${var.env}/app"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id

  secret_string = jsonencode({
    DB_USERNAME  = var.db_username
    DB_PASSWORD  = random_password.db.result
    DB_HOST      = aws_db_instance.postgres.address
    DB_PORT      = aws_db_instance.postgres.port
    DB_NAME      = var.db_name
    DATABASE_URL = "postgresql+psycopg://${var.db_username}:${random_password.db.result}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
  })
}

output "db_endpoint" {
  value = aws_db_instance.postgres.address
}

output "secret_name" {
  value = aws_secretsmanager_secret.app.name
}
