data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Execution role: pull ECR + logs + secrets injection
resource "aws_iam_role" "ecs_execution" {
  name               = "${var.project_name}-${var.env}-ecs-exec"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_exec_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Extra: allow read the specific secret
resource "aws_iam_role_policy" "ecs_exec_secret" {
  name = "${var.project_name}-${var.env}-ecs-exec-secret"
  role = aws_iam_role.ecs_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [aws_secretsmanager_secret.app.arn]
      }
    ]
  })
}

# Task role: permessi “app”. Starter: niente extra (lo allarghiamo quando serve)
resource "aws_iam_role" "ecs_task" {
  name               = "${var.project_name}-${var.env}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

