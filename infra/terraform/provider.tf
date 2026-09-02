terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # State is local by default (terraform.tfstate in this folder). Fine for
  # a single-person/single-environment setup. If this grows to a team
  # project, switch to an S3 backend with state locking -- see README.
}

provider "aws" {
  region = var.aws_region
}
