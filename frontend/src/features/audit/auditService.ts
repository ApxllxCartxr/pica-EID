import { apiClient } from '../../api/client';
import type { AuditLogListResponse } from '../../types';

export const auditService = {
    getAll: async (page = 1, per_page = 20): Promise<AuditLogListResponse> => {
        const response = await apiClient.get<AuditLogListResponse>('/audit', {
            params: { page, per_page },
        });
        return response.data;
    },

    export: async (): Promise<void> => {
        const response = await apiClient.get('/dashboard/audit/export', {
            responseType: 'blob',
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `audit_logs_${new Date().toISOString()}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    },
};
