import { apiClient } from '../../api/client';
import { Domain } from '../../types';

export const domainService = {
    getAll: async (include_deleted = false, deleted_only = false): Promise<Domain[]> => {
        const response = await apiClient.get<Domain[]>('/domains', {
            params: { include_deleted, deleted_only },
        });
        return response.data;
    },

    create: async (data: Partial<Domain>): Promise<Domain> => {
        const response = await apiClient.post<Domain>('/domains', data);
        return response.data;
    },

    update: async (id: number, data: Partial<Domain>): Promise<Domain> => {
        const response = await apiClient.put<Domain>(`/domains/${id}`, data);
        return response.data;
    },

    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/domains/${id}`);
    },

    restore: async (id: number): Promise<void> => {
        await apiClient.post(`/domains/${id}/restore`);
    },

    hardDelete: async (id: number): Promise<void> => {
        await apiClient.delete(`/domains/${id}/permanent`);
    },
};
