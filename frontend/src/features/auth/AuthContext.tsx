import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { LoginResponse } from '../../types';
import { AccessLevel } from '../../types';

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    username: string | null;
    accessLevel: AccessLevel | null;
    login: (response: LoginResponse) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [username, setUsername] = useState<string | null>(null);
    const [accessLevel, setAccessLevel] = useState<AccessLevel | null>(null);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const storedUsername = localStorage.getItem('username');
        const storedLevel = localStorage.getItem('access_level');
        if (token && storedUsername) {
            setIsAuthenticated(true);
            setUsername(storedUsername);
            setAccessLevel(storedLevel as AccessLevel);
        }
        setIsLoading(false);
    }, []);

    const login = (response: LoginResponse) => {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
        localStorage.setItem('username', response.username);
        localStorage.setItem('access_level', response.access_level);
        setIsAuthenticated(true);
        setUsername(response.username);
        setAccessLevel(response.access_level);
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('username');
        localStorage.removeItem('access_level');
        setIsAuthenticated(false);
        setUsername(null);
        setAccessLevel(null);
    };

    return (
        <AuthContext.Provider value={{ isAuthenticated, isLoading, username, accessLevel, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
