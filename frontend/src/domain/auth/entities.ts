/**
 * Auth Domain Entities for Frontend
 * 
 * TypeScript models that correspond to backend domain entities.
 * These are used for type safety and validation on the frontend.
 */

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING = 'pending',
}

export enum RoleType {
  ADMIN = 'admin',
  USER = 'user',
  MODERATOR = 'moderator',
  GUEST = 'guest',
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
  createdAt: Date;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  roleType: RoleType;
  createdAt: Date;
  updatedAt?: Date;
}

export interface User {
  id: string;
  email: string;
  name: string;
  roles: Role[];
  status: UserStatus;
  lastLogin?: Date;
  createdAt: Date;
  updatedAt?: Date;
  profileData: Record<string, any>;
  preferences: UserPreferences;
  
  // Computed properties
  permissions?: string[];
  roleNames?: string[];
  isAdmin?: boolean;
}

export interface UserPreferences {
  theme: 'light' | 'dark';
  language: 'en' | 'ru';
  notifications: boolean;
  timezone?: string;
  dateFormat?: string;
  emailNotifications?: boolean;
}

export interface AuthSession {
  id: string;
  userId: string;
  token: string;
  refreshToken: string;
  expiresAt: Date;
  createdAt: Date;
  isActive: boolean;
  ipAddress?: string;
  userAgent?: string;
}

// ============================================================================
// Utility Functions
// ============================================================================

export const hasPermission = (user: User, permission: string): boolean => {
  return user.permissions?.includes(permission) || false;
};

export const hasRole = (user: User, role: string): boolean => {
  return user.roleNames?.includes(role) || false;
};

export const isUserActive = (user: User): boolean => {
  return user.status === UserStatus.ACTIVE;
};

export const isUserAdmin = (user: User): boolean => {
  return user.roles.some(role => role.roleType === RoleType.ADMIN);
};

export const getUserPermissions = (user: User): string[] => {
  const permissions = new Set<string>();
  
  user.roles.forEach(role => {
    role.permissions.forEach(permission => {
      permissions.add(permission.name);
    });
  });
  
  return Array.from(permissions);
};

export const getUserRoleNames = (user: User): string[] => {
  return user.roles.map(role => role.name);
};

// ============================================================================
// Validation Functions
// ============================================================================

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

export const validateUserName = (name: string): boolean => {
  return name.trim().length >= 2;
};

// ============================================================================
// Factory Functions
// ============================================================================

export const createUser = (userData: Partial<User>): User => {
  const defaultPreferences: UserPreferences = {
    theme: 'light',
    language: 'en',
    notifications: true,
  };

  return {
    id: userData.id || '',
    email: userData.email || '',
    name: userData.name || '',
    roles: userData.roles || [],
    status: userData.status || UserStatus.ACTIVE,
    createdAt: userData.createdAt || new Date(),
    profileData: userData.profileData || {},
    preferences: { ...defaultPreferences, ...userData.preferences },
    lastLogin: userData.lastLogin,
    updatedAt: userData.updatedAt,
    
    // Computed properties
    permissions: getUserPermissions(userData as User),
    roleNames: getUserRoleNames(userData as User),
    isAdmin: isUserAdmin(userData as User),
  };
};

export const createRole = (roleData: Partial<Role>): Role => {
  return {
    id: roleData.id || '',
    name: roleData.name || '',
    description: roleData.description || '',
    permissions: roleData.permissions || [],
    roleType: roleData.roleType || RoleType.USER,
    createdAt: roleData.createdAt || new Date(),
    updatedAt: roleData.updatedAt,
  };
};

export const createPermission = (permissionData: Partial<Permission>): Permission => {
  return {
    id: permissionData.id || '',
    name: permissionData.name || '',
    description: permissionData.description || '',
    resource: permissionData.resource || '',
    action: permissionData.action || '',
    createdAt: permissionData.createdAt || new Date(),
  };
}; 