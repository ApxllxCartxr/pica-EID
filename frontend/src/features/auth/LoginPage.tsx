import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { authService, loginSchema, type LoginInput } from './authService';
import { useAuth } from './AuthContext';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Shield } from 'lucide-react';

export default function LoginPage() {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [error, setError] = useState('');

    const { register, handleSubmit, formState: { errors } } = useForm<LoginInput>({
        resolver: zodResolver(loginSchema),
    });

    const mutation = useMutation({
        mutationFn: authService.login,
        onSuccess: (data) => {
            login(data);
            navigate('/dashboard');
        },
        onError: (err: unknown) => {
            const error = err as { response?: { data?: { detail?: string } } };
            setError(error.response?.data?.detail || 'Login failed. Please try again.');
        },
    });

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            {/* Background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-purple-500/5" />

            <div className="relative w-full max-w-md space-y-8">
                {/* Logo */}
                <div className="text-center">
                    <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25 mb-6">
                        <Shield className="h-8 w-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">PRISMID</h1>
                    <p className="mt-2 text-slate-400">Sign in to your account</p>
                </div>

                {/* Form */}
                <div className="rounded-xl border border-white/10 bg-slate-900/50 backdrop-blur-xl p-8 shadow-2xl">
                    <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-5">
                        {error && (
                            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3">
                                <p className="text-sm text-red-400">{error}</p>
                            </div>
                        )}

                        <Input
                            id="username"
                            label="Username"
                            placeholder="Enter your username"
                            error={errors.username?.message}
                            {...register('username')}
                        />

                        <Input
                            id="password"
                            type="password"
                            label="Password"
                            placeholder="Enter your password"
                            error={errors.password?.message}
                            {...register('password')}
                        />

                        <Button type="submit" className="w-full" isLoading={mutation.isPending}>
                            Sign In
                        </Button>
                    </form>
                </div>
            </div>
        </div>
    );
}
