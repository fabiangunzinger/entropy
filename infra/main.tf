
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }
  required_version = ">= 0.14.9"
}

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

resource "aws_instance" "vm" {
  ami                  = var.instance_ami
  instance_type        = var.instance_type
  security_groups      = [aws_security_group.traffic_rules.name]
  iam_instance_profile = aws_iam_instance_profile.iam_profile.name
  key_name             = var.instance_key_pair
  user_data            = file("vm-setup.sh")

  tags = {
    Name = var.instance_name
  }
}

resource "aws_security_group" "traffic_rules" {
  name        = "${var.instance_name}-traffic_rules"
  description = "Rules for inbound and outbound instance access."

  # ssh inbound access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["92.2.118.89/32"]
  }

  # allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_instance_profile" "iam_profile" {
  name = "${var.instance_name}_iam_profile"
  role = aws_iam_role.iam_role.name
}

resource "aws_iam_role" "iam_role" {
  name = "${var.instance_name}-iam-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
      "Service": "ec2.amazonaws.com"
    },
    "Effect": "Allow",
    "Sid": ""
  }
]
}
EOF
}

resource "aws_iam_role_policy_attachment" "attach" {
  role       = aws_iam_role.iam_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}


