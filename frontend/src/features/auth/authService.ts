import { apiClient } from '../../api/client';
import type { LoginResponse } from '../../types';
import { z } from 'zod';

export const loginSchema = z.object({
    username: z.string().min(1, 'Username is required'),
    password: z.string().min(1, 'Password is required'),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const authService = {
    login: async (data: LoginInput): Promise<LoginResponse> => {
        const response = await apiClient.post<LoginResponse>('/auth/login', data);
        return response.data;
    },

    logout: async (): Promise<void> => {
        try {
            await apiClient.post('/auth/logout');
        } catch {
            // Best effort
        }
    },

    getMe: async (): Promise<{ username: string; access_level: string }> => {
        const response = await apiClient.get('/auth/me');
        return response.data;
    },

    changePassword: async (data: any): Promise<void> => {
        await apiClient.post('/auth/change-password', data);
    },
};
