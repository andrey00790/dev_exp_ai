# Terraform Outputs for AI Assistant MVP Infrastructure

# Network Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

# Load Balancer Outputs
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Hosted zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "backend_target_group_arn" {
  description = "ARN of the backend target group"
  value       = aws_lb_target_group.backend.arn
}

output "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  value       = aws_lb_target_group.frontend.arn
}

# Database Outputs
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "rds_port" {
  description = "RDS port"
  value       = aws_db_instance.main.port
}

# Redis Outputs
output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_auth_token" {
  description = "ElastiCache Redis auth token"
  value       = var.redis_auth_token
  sensitive   = true
}

# ECS Outputs
output "ecs_cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "backend_service_name" {
  description = "Backend ECS service name"
  value       = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  description = "Frontend ECS service name"
  value       = aws_ecs_service.frontend.name
}

output "backend_task_definition_arn" {
  description = "Backend task definition ARN"
  value       = aws_ecs_task_definition.backend.arn
}

output "frontend_task_definition_arn" {
  description = "Frontend task definition ARN"
  value       = aws_ecs_task_definition.frontend.arn
}

# IAM Outputs
output "ecs_task_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = aws_iam_role.ecs_task_role.arn
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ECS tasks security group ID"
  value       = aws_security_group.ecs_tasks.id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

output "redis_security_group_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}

# S3 Outputs
output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.main.bucket
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.main.arn
}

# CloudWatch Outputs
output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "cloudwatch_log_group_arn" {
  description = "CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.ecs.arn
}

# Auto Scaling Outputs
output "backend_autoscaling_target_resource_id" {
  description = "Backend auto scaling target resource ID"
  value       = aws_appautoscaling_target.backend.resource_id
}

output "frontend_autoscaling_target_resource_id" {
  description = "Frontend auto scaling target resource ID"
  value       = aws_appautoscaling_target.frontend.resource_id
}

# SSM Parameter Outputs
output "secret_key_parameter_name" {
  description = "SSM parameter name for secret key"
  value       = aws_ssm_parameter.secret_key.name
}

output "jwt_secret_parameter_name" {
  description = "SSM parameter name for JWT secret"
  value       = aws_ssm_parameter.jwt_secret.name
}

# Environment Configuration Summary
output "environment_summary" {
  description = "Summary of deployed environment"
  value = {
    environment    = var.environment
    project_name   = var.project_name
    aws_region     = var.aws_region
    vpc_cidr       = var.vpc_cidr
    
    # Service URLs
    application_url = var.domain_name != null ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"
    api_url        = var.domain_name != null ? "https://${var.domain_name}/api" : "http://${aws_lb.main.dns_name}/api"
    
    # Resource counts
    availability_zones     = length(data.aws_availability_zones.available.names)
    public_subnets        = length(aws_subnet.public)
    private_subnets       = length(aws_subnet.private)
    
    # Service configuration
    backend_desired_count  = var.backend_desired_count
    frontend_desired_count = var.frontend_desired_count
    backend_cpu           = var.backend_cpu
    backend_memory        = var.backend_memory
    
    # Database configuration
    db_instance_class         = var.db_instance_class
    db_allocated_storage      = var.db_allocated_storage
    db_backup_retention_days  = var.db_backup_retention_period
    
    # Cache configuration
    redis_node_type          = var.redis_node_type
    redis_num_cache_clusters = var.redis_num_cache_clusters
    
    # Monitoring
    log_retention_days = var.log_retention_in_days
  }
}

# Connection Information (for deployment scripts)
output "connection_info" {
  description = "Connection information for deployment and monitoring"
  value = {
    # Database connection
    database_url = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}:${aws_db_instance.main.port}/${var.db_name}"
    
    # Redis connection
    redis_url = "redis://:${var.redis_auth_token}@${aws_elasticache_replication_group.main.primary_endpoint_address}:${aws_elasticache_replication_group.main.port}"
    
    # ECS connection info
    ecs_cluster = aws_ecs_cluster.main.name
    backend_service = aws_ecs_service.backend.name
    frontend_service = aws_ecs_service.frontend.name
    
    # Monitoring
    log_group = aws_cloudwatch_log_group.ecs.name
    
    # Load balancer
    load_balancer_dns = aws_lb.main.dns_name
  }
  sensitive = true
}

# Resource Tags Summary
output "applied_tags" {
  description = "Tags applied to all resources"
  value = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Version     = "2.1.0"
  }
} 