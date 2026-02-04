variable "aws_region" {
  type    = string
  default = "eu-north-1"
}

variable "project_name" {
  type    = string
  default = "bali"
}

variable "env" {
  type    = string
  default = "dev"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "db_name" {
  type    = string
  default = "postgres"
}

variable "db_username" {
  type    = string
  default = "bali_admin"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

