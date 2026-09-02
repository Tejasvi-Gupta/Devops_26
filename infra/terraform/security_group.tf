# Only open what's actually needed: SSH for management, and the ports our
# docker-compose.yml publishes (frontend on 5173, backend API on 8000).
# Postgres (5432) is deliberately NOT opened here -- it only needs to be
# reachable from the backend container on the same host, not the internet.

resource "aws_security_group" "app" {
  name        = "${var.project_name}-sg"
  description = "Allow SSH, frontend, and backend API access"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  ingress {
    description = "Frontend (nginx)"
    from_port   = 5173
    to_port     = 5173
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Backend API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound (package installs, Docker pulls, etc.)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}
