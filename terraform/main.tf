terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    region = "eu-west-2"
    bucket = "de-gdpr-obfuscator-terraform-statefiles" # REPLACE with your bucket
    key    = "extract-statefile"
  }
}

provider "aws" {
  region = "eu-west-2"
}

# Get account and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
