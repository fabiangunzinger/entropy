
variable "aws_profile" {
    description = "AWS profile name"
    type        = string
    default     = "3di"
}

variable "aws_region" {
    description = "AWS region"
    type        = string
    default     = "eu-west-2"   # london
}

variable "instance_name" {
    description = "Value of the Name tag for the EC2 instance"
    type        = string
    default     = "entropy"
}

variable "instance_type" {
    description = "EC2 instance type"
    type        = string
    default     = "t2.micro"
}

variable "instance_ami" {
    description = "AWS machine image id"
    type        = string
    default     = "ami-0194c3e07668a7e36"   # basic ubuntu
}

variable "instance_key_pair" {
    description = "AWS key pair used to access instance"
    type        = string
    default     = "ec2-tracker-fgu"
}

