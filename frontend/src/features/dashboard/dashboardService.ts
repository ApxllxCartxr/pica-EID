import { apiClient } from '../../api/client';
import type { DashboardStats, DashboardTrend } from '../../types';

export const dashboardService = {
    getStats: async (): Promise<DashboardStats> => {
        const response = await apiClient.get<DashboardStats>('/dashboard/stats');
        return response.data;
    },

    getTrend: async (days = 30): Promise<DashboardTrend> => {
        const response = await apiClient.get<DashboardTrend>('/dashboard/stats/trend', {
            params: { days },
        });
        return response.data;
    },

    getWarnings: async () => {
        const response = await apiClient.get('/dashboard/warnings');
        return response.data;
    },
};
