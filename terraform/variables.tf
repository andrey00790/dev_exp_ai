# Terraform Variables for AI Assistant MVP Infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "ai-assistant-mvp"
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
  
  validation {
    condition = can(regex("^db\\.", var.db_instance_class))
    error_message = "DB instance class must start with 'db.'."
  }
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS (GB)"
  type        = number
  default     = 20
  
  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 1000
    error_message = "DB allocated storage must be between 20 and 1000 GB."
  }
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS auto-scaling (GB)"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ai_assistant"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters long."
  }
}

variable "db_backup_retention_period" {
  description = "Database backup retention period (days)"
  type        = number
  default     = 7
  
  validation {
    condition     = var.db_backup_retention_period >= 1 && var.db_backup_retention_period <= 35
    error_message = "Backup retention period must be between 1 and 35 days."
  }
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_clusters" {
  description = "Number of cache clusters (1 for single node, 2+ for HA)"
  type        = number
  default     = 1
  
  validation {
    condition     = var.redis_num_cache_clusters >= 1 && var.redis_num_cache_clusters <= 6
    error_message = "Number of cache clusters must be between 1 and 6."
  }
}

variable "redis_auth_token" {
  description = "Auth token for Redis (must be 32-128 chars)"
  type        = string
  sensitive   = true
  default     = "SuperSecureRedisAuthToken2024!"
  
  validation {
    condition     = length(var.redis_auth_token) >= 16 && length(var.redis_auth_token) <= 128
    error_message = "Redis auth token must be between 16 and 128 characters."
  }
}

# ECS Configuration
variable "backend_cpu" {
  description = "CPU units for backend task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
  
  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.backend_cpu)
    error_message = "CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "backend_memory" {
  description = "Memory (MB) for backend task"
  type        = number
  default     = 1024
  
  validation {
    condition     = var.backend_memory >= 512 && var.backend_memory <= 8192
    error_message = "Memory must be between 512 and 8192 MB."
  }
}

variable "frontend_cpu" {
  description = "CPU units for frontend task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory (MB) for frontend task"
  type        = number
  default     = 512
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 2
  
  validation {
    condition     = var.backend_desired_count >= 1 && var.backend_desired_count <= 10
    error_message = "Desired count must be between 1 and 10."
  }
}

variable "frontend_desired_count" {
  description = "Desired number of frontend tasks"
  type        = number
  default     = 2
}

# Container Images
variable "backend_image" {
  description = "Docker image for backend"
  type        = string
  default     = "ai-assistant-backend:latest"
}

variable "frontend_image" {
  description = "Docker image for frontend"
  type        = string
  default     = "ai-assistant-frontend:latest"
}

# Monitoring Configuration
variable "log_retention_in_days" {
  description = "CloudWatch log retention period"
  type        = number
  default     = 14
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_in_days)
    error_message = "Log retention must be a valid CloudWatch retention period."
  }
}

variable "enable_performance_insights" {
  description = "Enable RDS Performance Insights"
  type        = bool
  default     = true
}

variable "enable_enhanced_monitoring" {
  description = "Enable RDS Enhanced Monitoring"
  type        = bool
  default     = true
}

# Auto Scaling Configuration
variable "backend_min_capacity" {
  description = "Minimum number of backend tasks"
  type        = number
  default     = 1
}

variable "backend_max_capacity" {
  description = "Maximum number of backend tasks"
  type        = number
  default     = 10
}

variable "frontend_min_capacity" {
  description = "Minimum number of frontend tasks"
  type        = number
  default     = 1
}

variable "frontend_max_capacity" {
  description = "Maximum number of frontend tasks"
  type        = number
  default     = 5
}

variable "cpu_target_value" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70.0
  
  validation {
    condition     = var.cpu_target_value >= 10.0 && var.cpu_target_value <= 90.0
    error_message = "CPU target value must be between 10.0 and 90.0."
  }
}

variable "memory_target_value" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80.0
}

# Security Configuration
variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access ALB"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Open to internet, restrict in production
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for HTTPS"
  type        = string
  default     = null
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = null
}

# Environment-specific configurations
locals {
  environment_config = {
    development = {
      db_instance_class           = "db.t3.micro"
      db_allocated_storage        = 20
      db_backup_retention_period  = 1
      redis_node_type            = "cache.t3.micro"
      redis_num_cache_clusters   = 1
      backend_cpu                = 256
      backend_memory             = 512
      frontend_cpu               = 256
      frontend_memory            = 512
      backend_desired_count      = 1
      frontend_desired_count     = 1
      log_retention_in_days      = 7
      enable_deletion_protection = false
    }
    staging = {
      db_instance_class           = "db.t3.small"
      db_allocated_storage        = 50
      db_backup_retention_period  = 3
      redis_node_type            = "cache.t3.small"
      redis_num_cache_clusters   = 1
      backend_cpu                = 512
      backend_memory             = 1024
      frontend_cpu               = 256
      frontend_memory            = 512
      backend_desired_count      = 1
      frontend_desired_count     = 1
      log_retention_in_days      = 14
      enable_deletion_protection = false
    }
    production = {
      db_instance_class           = "db.t3.medium"
      db_allocated_storage        = 100
      db_backup_retention_period  = 7
      redis_node_type            = "cache.t3.medium"
      redis_num_cache_clusters   = 2
      backend_cpu                = 1024
      backend_memory             = 2048
      frontend_cpu               = 512
      frontend_memory            = 1024
      backend_desired_count      = 2
      frontend_desired_count     = 2
      log_retention_in_days      = 30
      enable_deletion_protection = true
    }
  }
}

# Environment defaults
variable "use_environment_defaults" {
  description = "Use environment-specific default values"
  type        = bool
  default     = true
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
} 