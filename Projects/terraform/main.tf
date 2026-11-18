
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

resource "aws_iam_role" "glue_execution" {
  name = "FSAPGlueExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "glue.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project     = "FinancialSalesAnalyticsPipeline"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

resource "aws_iam_role_policy" "fsap_bucket_access" {
  name = "FSAPBucketAccess"
  role = aws_iam_role.glue_execution.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]

        Resource = aws_s3_bucket.fsap_data.arn
      },
      {
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]

        Resource = "${aws_s3_bucket.fsap_data.arn}/*"
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}



resource "aws_glue_job" "financial_sales_etl" {
  name     = "fsap-financial-sales-etl"
  role_arn = aws_iam_role.glue_execution.arn

  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30
  max_retries       = 0

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${aws_s3_bucket.fsap_data.bucket}/scripts/etl_pipeline.py"
  }

  default_arguments = {
    "--job-language" = "python"

    "--RAW_PATH" = "s3://${aws_s3_bucket.fsap_data.bucket}/input/sales_events.csv"

    "--CURATED_PATH" = "s3://${aws_s3_bucket.fsap_data.bucket}/output/curated/"

    "--QUARANTINE_PATH" = "s3://${aws_s3_bucket.fsap_data.bucket}/output/quarantine/"

    "--SUPERSEDED_PATH" = "s3://${aws_s3_bucket.fsap_data.bucket}/output/superseded/"

    "--AGGREGATE_PATH" = "s3://${aws_s3_bucket.fsap_data.bucket}/output/monthly_sales/"

    "--extra-py-files" = "s3://${aws_s3_bucket.fsap_data.bucket}/scripts/financial_pipeline.py"

    "--enable-continuous-cloudwatch-log" = "true"
  }
}
