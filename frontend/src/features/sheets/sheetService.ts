import { apiClient } from '../../api/client';
import type { SyncLogListResponse } from '../../types';

export const sheetService = {
    sync: async (): Promise<{ message: string; task_id: string }> => {
        const response = await apiClient.post<{ message: string; task_id: string }>('/sheets/sync-google');
        return response.data;
    },

    getLogs: async (page = 1, per_page = 10): Promise<SyncLogListResponse> => {
        const response = await apiClient.get<SyncLogListResponse>('/sheets/logs', {
            params: { page, per_page },
        });
        return response.data;
    },
};
