terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "backups" {
  bucket = "logiflow-wms-backups"
  tags = {
    Project = "LogiFlow WMS"
    Purpose = "Local backup practice"
  }
}