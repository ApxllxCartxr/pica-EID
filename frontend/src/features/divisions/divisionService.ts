import { apiClient } from '../../api/client';
import { Division } from '../../types';

export const divisionService = {
    getAll: async (include_deleted = false, deleted_only = false): Promise<Division[]> => {
        const response = await apiClient.get<Division[]>('/divisions', {
            params: { include_deleted, deleted_only },
        });
        return response.data;
    },

    create: async (data: Partial<Division>): Promise<Division> => {
        const response = await apiClient.post<Division>('/divisions', data);
        return response.data;
    },

    update: async (id: number, data: Partial<Division>): Promise<Division> => {
        const response = await apiClient.put<Division>(`/divisions/${id}`, data);
        return response.data;
    },

    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/divisions/${id}`);
    },

    restore: async (id: number): Promise<void> => {
        await apiClient.post(`/divisions/${id}/restore`);
    },

    hardDelete: async (id: number): Promise<void> => {
        await apiClient.delete(`/divisions/${id}/permanent`);
    },
};
