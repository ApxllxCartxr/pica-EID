export enum UserCategory {
    INTERN = "INTERN",
    EMPLOYEE = "EMPLOYEE",
}

export enum UserStatus {
    ACTIVE = "ACTIVE",
    INACTIVE = "INACTIVE",
    EXPIRED = "EXPIRED",
    CONVERTED = "CONVERTED",
}

export enum AccessLevel {
    VIEWER = "VIEWER",
    ADMIN = "ADMIN",
    SUPERADMIN = "SUPERADMIN",
}

export interface Domain {
    id: number;
    name: string;
    description?: string | null;
    is_active: boolean;
    deleted_at?: string | null;
}

export interface Division {
    id: number;
    name: string;
    description?: string | null;
    is_active: boolean;
    deleted_at?: string | null;
}

export interface UserRole {
    id: number;
    user_id: number;
    role_id: number;
    role: Role;
    assigned_at: string;
}

export interface User {
    id: number;
    ulid: string;
    display_id: string;
    name: string;
    email: string;
    phone_number?: string | null;
    category: UserCategory;
    status: UserStatus;
    domain?: Domain | null;
    division?: Division | null;
    user_roles?: UserRole[];
    domain_name?: string | null;
    division_name?: string | null;
    roles: string[];
    conversion_date?: string | null;
    date_of_joining?: string | null;
    start_date?: string | null;
    end_date?: string | null;
    created_at: string;
    deleted_at?: string | null;
}

export interface UserCreateRequest {
    name: string;
    email: string;
    phone_number?: string;
    category: UserCategory;
    domain_id?: number | null;
    division_id?: number | null;
    date_of_joining?: string | null;
    start_date?: string | null;
    end_date?: string | null;
    role_ids?: number[];
}

export interface UserUpdateRequest {
    name?: string;
    email?: string;
    phone_number?: string;
    domain_id?: number | null;
    division_id?: number | null;
    date_of_joining?: string | null;
    status?: UserStatus;
    version?: number;
}

export interface UserSearchResponse {
    users: User[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
}

export interface Role {
    id: number;
    name: string;
    description?: string | null;
    clearance_level: number;
    is_active: boolean;
    assigned_users_count: number;
    created_at: string;
}

export interface RoleCreateRequest {
    name: string;
    description?: string | null;
    clearance_level?: number;
    is_active?: boolean;
}

export interface RoleUpdateRequest {
    name?: string;
    description?: string | null;
    clearance_level?: number;
    is_active?: boolean;
    version?: number;
}

export interface RoleListResponse {
    roles: Role[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
}

export interface AuditLog {
    id: number;
    user_id: number;
    action: string;
    resource_type: string;
    resource_id?: string;
    details?: unknown;
    ip_address?: string;
    user_agent?: string;
    created_at: string;
    user?: {
        name: string;
        email: string;
    };
}

export interface AuditLogListResponse {
    logs: AuditLog[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
}

export interface SyncLog {
    id: number;
    started_at: string;
    completed_at?: string;
    status: 'SUCCESS' | 'FAILURE' | 'IN_PROGRESS';
    details?: unknown;
    created_at: string;
}

export interface SyncLogListResponse {
    logs: SyncLog[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
}

export interface LoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    access_level: AccessLevel;
    username: string;
}

export interface UserSearchQuery {
    q?: string;
    page: number;
    per_page: number;
    category?: string;
    status?: string;
    include_deleted?: boolean;
}

export interface DashboardStats {
    total_users: number;
    active_users: number;
    total_interns: number;
    total_employees: number;
    total_roles: number;
    recent_actions: {
        action: string;
        entity_type: string;
        entity_id: string | null;
        timestamp: string;
    }[];
}

export interface DashboardTrend {
    trend: {
        date: string;
        count: number;
    }[];
    days: number;
}
