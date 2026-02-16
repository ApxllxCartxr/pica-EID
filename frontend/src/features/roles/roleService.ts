import { apiClient } from '../../api/client';
import type {
    RoleListResponse,
    RoleCreateRequest,
    RoleUpdateRequest,
    Role,
} from '../../types';

export const roleService = {
    getAll: async (page = 1, per_page = 20, include_deleted = false, deleted_only = false): Promise<RoleListResponse> => {
        const response = await apiClient.get<RoleListResponse>('/roles', {
            params: { page, per_page, include_deleted, deleted_only },
        });
        return response.data;
    },

    create: async (data: RoleCreateRequest): Promise<Role> => {
        const response = await apiClient.post<Role>('/roles', data);
        return response.data;
    },

    update: async (id: number, data: RoleUpdateRequest): Promise<Role> => {
        const response = await apiClient.put<Role>(`/roles/${id}`, data);
        return response.data;
    },

    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/roles/${id}`);
    },

    restore: async (id: number): Promise<void> => {
        await apiClient.post(`/roles/${id}/restore`);
    },

    hardDelete: async (id: number): Promise<void> => {
        await apiClient.delete(`/roles/${id}/permanent`);
    },
};
