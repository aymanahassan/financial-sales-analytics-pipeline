
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region  = "eu-north-1"
  profile = "fsap"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "fsap_data" {
  bucket = "fsap-financial-sales-dev-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project     = "FinancialSalesAnalyticsPipeline"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket_public_access_block" "fsap_data" {
  bucket = aws_s3_bucket.fsap_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "fsap_bucket_name" {
  description = "S3 bucket for the FSAP data pipeline"
  value       = aws_s3_bucket.fsap_data.bucket
}

output "aws_account_id" {
  description = "AWS account targeted by Terraform"
  value       = data.aws_caller_identity.current.account_id
}
