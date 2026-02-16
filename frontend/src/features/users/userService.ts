import { apiClient } from '../../api/client';
import type {
    UserSearchResponse,
    UserCreateRequest,
    UserUpdateRequest,
    User,
} from '../../types';

export const userService = {
    search: async (
        query = '',
        page = 1,
        per_page = 10,
        category?: string,
        status?: string | string[],
        include_deleted = false,
        deleted_only = false
    ): Promise<UserSearchResponse> => {
        const response = await apiClient.get<UserSearchResponse>('/users', {
            params: {
                q: query,
                page,
                per_page,
                category,
                status,
                include_deleted,
                deleted_only
            },
            paramsSerializer: {
                indexes: null // Ensure arrays are serialized as status=a&status=b
            }
        });
        return response.data;
    },

    getById: async (id: number): Promise<User> => {
        const response = await apiClient.get<User>(`/users/${id}`);
        return response.data;
    },

    create: async (data: UserCreateRequest): Promise<User> => {
        const response = await apiClient.post<User>('/users', data);
        return response.data;
    },

    update: async (id: string, data: UserUpdateRequest): Promise<User> => {
        const response = await apiClient.put<User>(`/users/${id}`, data);
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/users/${id}`);
    },

    restore: async (id: string): Promise<User> => {
        const response = await apiClient.post<User>(`/users/${id}/restore`);
        return response.data;
    },

    hardDelete: async (id: string): Promise<void> => {
        await apiClient.delete(`/users/${id}/permanent`);
    },

    convert: async (id: string): Promise<User> => {
        const response = await apiClient.post<User>(`/users/${id}/convert`, {});
        return response.data;
    },

    endInternship: async (id: string): Promise<User> => {
        const response = await apiClient.post<User>(`/users/${id}/end-internship`, {});
        return response.data;
    },

    retire: async (id: string): Promise<User> => {
        const response = await apiClient.post<User>(`/users/${id}/retire`, {});
        return response.data;
    },

    export: async (): Promise<void> => {
        // 1. Trigger export generation
        const { data: { download_url, filename } } = await apiClient.post<{ download_url: string; filename: string }>('/sheets/export', {});

        // 2. Fetch the file using authenticated client
        const response = await apiClient.get(download_url, {
            responseType: 'blob',
        });

        // 3. Create blob link to download
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename); // Use filename from step 1
        document.body.appendChild(link);
        link.click();

        // 4. Cleanup
        link.remove();
        window.URL.revokeObjectURL(url);
    },
};
