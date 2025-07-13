"""
Auth Domain Services

Domain services that implement business logic that doesn't naturally
belong to a single entity or value object.
"""

from typing import Dict, Any, Optional
import re


class AuthDomainService:
    """
    Domain service for authentication-related business logic.
    
    This service contains domain logic that spans multiple entities
    or doesn't belong to a specific entity.
    """
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength according to business rules.
        
        Args:
            password: The password to validate
            
        Returns:
            Dictionary with strength assessment
        """
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 2
        elif len(password) >= 6:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")
        
        # Character variety checks
        if re.search(r"[a-z]", password):
            score += 1
        else:
            feedback.append("Password should contain lowercase letters")
            
        if re.search(r"[A-Z]", password):
            score += 1
        else:
            feedback.append("Password should contain uppercase letters")
            
        if re.search(r"\d", password):
            score += 1
        else:
            feedback.append("Password should contain numbers")
            
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            score += 1
            feedback.append("Great! Contains special characters")
        
        # Determine strength level
        if score >= 6:
            strength = "strong"
        elif score >= 4:
            strength = "medium"
        else:
            strength = "weak"
        
        return {
            "strength": strength,
            "score": score,
            "max_score": 6,
            "feedback": feedback,
            "is_valid": score >= 4
        }
    
    def generate_username_suggestions(self, email: str, name: str) -> list[str]:
        """
        Generate username suggestions based on email and name.
        
        Args:
            email: User's email address
            name: User's full name
            
        Returns:
            List of suggested usernames
        """
        suggestions = []
        
        # From email
        email_part = email.split('@')[0]
        suggestions.append(email_part)
        
        # From name
        name_parts = name.lower().split()
        if len(name_parts) >= 2:
            suggestions.append(f"{name_parts[0]}.{name_parts[1]}")
            suggestions.append(f"{name_parts[0]}{name_parts[1]}")
            suggestions.append(f"{name_parts[0][0]}{name_parts[1]}")
        elif len(name_parts) == 1:
            suggestions.append(name_parts[0])
        
        # Add numbers to avoid conflicts
        numbered_suggestions = []
        for suggestion in suggestions:
            numbered_suggestions.extend([
                suggestion,
                f"{suggestion}123",
                f"{suggestion}2024"
            ])
        
        return list(set(numbered_suggestions))  # Remove duplicates
    
    def is_password_compromised(self, password: str) -> bool:
        """
        Check if password appears in common password lists.
        
        In a real implementation, this would check against
        a database of compromised passwords (like HaveIBeenPwned).
        
        Args:
            password: Password to check
            
        Returns:
            True if password is compromised
        """
        # Common weak passwords
        weak_passwords = {
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "dragon", "password1"
        }
        
        return password.lower() in weak_passwords
    
    def calculate_account_security_score(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall account security score.
        
        Args:
            user_data: Dictionary with user information
            
        Returns:
            Security assessment
        """
        score = 0
        max_score = 10
        recommendations = []
        
        # Password strength (40% weight)
        password_strength = user_data.get("password_strength", {})
        if password_strength.get("strength") == "strong":
            score += 4
        elif password_strength.get("strength") == "medium":
            score += 2
            recommendations.append("Consider using a stronger password")
        else:
            score += 0
            recommendations.append("Use a stronger password with mixed characters")
        
        # Two-factor authentication (30% weight)
        if user_data.get("has_2fa", False):
            score += 3
        else:
            recommendations.append("Enable two-factor authentication")
        
        # Email verification (20% weight)
        if user_data.get("email_verified", False):
            score += 2
        else:
            recommendations.append("Verify your email address")
        
        # Recent activity (10% weight)
        if user_data.get("recent_login", False):
            score += 1
        
        # Determine security level
        if score >= 8:
            level = "excellent"
        elif score >= 6:
            level = "good"
        elif score >= 4:
            level = "fair"
        else:
            level = "poor"
        
        return {
            "score": score,
            "max_score": max_score,
            "percentage": int((score / max_score) * 100),
            "level": level,
            "recommendations": recommendations
        }


class PasswordService:
    """
    Specialized domain service for password operations.
    """
    
    @staticmethod
    def generate_temporary_password(length: int = 12) -> str:
        """
        Generate a temporary password for password reset.
        
        Args:
            length: Password length
            
        Returns:
            Generated password
        """
        import secrets
        import string
        
        # Ensure password has variety
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        # Ensure at least one of each type
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-2] + secrets.choice(string.ascii_lowercase) + password[-1]
        if not any(c.isdigit() for c in password):
            password = password[:-3] + secrets.choice(string.digits) + password[-2:]
        
        return password
    
    @staticmethod
    def estimate_crack_time(password: str) -> Dict[str, Any]:
        """
        Estimate time to crack password.
        
        Args:
            password: Password to analyze
            
        Returns:
            Crack time estimation
        """
        # Character set size
        charset_size = 0
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
            charset_size += 20
        
        # Calculate possible combinations
        combinations = charset_size ** len(password)
        
        # Assume 1 billion attempts per second
        attempts_per_second = 1_000_000_000
        seconds_to_crack = combinations / (2 * attempts_per_second)  # Average case
        
        # Convert to human readable time
        if seconds_to_crack < 60:
            time_str = f"{seconds_to_crack:.1f} seconds"
        elif seconds_to_crack < 3600:
            time_str = f"{seconds_to_crack/60:.1f} minutes"
        elif seconds_to_crack < 86400:
            time_str = f"{seconds_to_crack/3600:.1f} hours"
        elif seconds_to_crack < 31536000:
            time_str = f"{seconds_to_crack/86400:.1f} days"
        else:
            time_str = f"{seconds_to_crack/31536000:.1f} years"
        
        return {
            "combinations": combinations,
            "seconds": seconds_to_crack,
            "human_readable": time_str,
            "charset_size": charset_size
        } 