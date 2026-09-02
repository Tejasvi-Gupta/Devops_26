variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1" # Mumbai -- closest region for low latency from India
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small" # 2 vCPU, 2GB RAM -- enough for Postgres + backend + frontend containers
}

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair, used for SSH access. Create one in the AWS Console (EC2 -> Key Pairs) first, then set this to its name."
  type        = string
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed to SSH into the instance. Defaults to open (0.0.0.0/0) for simplicity -- restrict this to your own IP for better security once you know it (e.g. \"203.0.113.4/32\")."
  type        = string
  default     = "0.0.0.0/0"
}

variable "project_name" {
  description = "Used to tag/name all resources"
  type        = string
  default     = "student-env-platform"
}

variable "repo_url" {
  description = "GitHub repo URL to clone on the instance (must be public, or the instance needs credentials configured separately for a private repo)"
  type        = string
}
