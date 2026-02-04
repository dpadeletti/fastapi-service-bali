resource "random_password" "db" {
  length  = 24
  special = true
}

resource "aws_db_subnet_group" "db" {
  name       = "${var.project_name}-${var.env}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-${var.env}-db"
  engine                 = "postgres"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  db_subnet_group_name   = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  publicly_accessible = false
  skip_final_snapshot = true

  # per starter: riduciamo “sorprese”
  deletion_protection = false
}

resource "aws_secretsmanager_secret" "app" {
  name = "${var.project_name}/${var.env}/app"
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

