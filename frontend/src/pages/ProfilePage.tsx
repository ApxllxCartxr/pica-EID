import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { authService } from '../features/auth/authService';
import { Button } from '../components/ui/Button';
import { Loader2, Shield, User, Key } from 'lucide-react';
import { toast } from 'react-hot-toast';

export default function ProfilePage() {
    const { data: user, isLoading } = useQuery({
        queryKey: ['me'],
        queryFn: authService.getMe,
    });

    const [passwordData, setPasswordData] = useState({
        current_password: '',
        new_password: '',
        confirm_password: '',
    });

    const changePasswordMutation = useMutation({
        mutationFn: authService.changePassword,
        onSuccess: () => {
            toast.success('Password changed successfully');
            setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to change password');
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (passwordData.new_password !== passwordData.confirm_password) {
            toast.error('New passwords do not match');
            return;
        }
        changePasswordMutation.mutate({
            current_password: passwordData.current_password,
            new_password: passwordData.new_password,
        });
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-96">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
            <h1 className="text-3xl font-bold tracking-tight text-white mb-2">My Profile</h1>

            {/* Profile Info Card */}
            <div className="bg-slate-900/40 border border-white/5 rounded-xl p-6 backdrop-blur-sm">
                <div className="flex items-center gap-4 mb-6">
                    <div className="h-16 w-16 rounded-full bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                        <User className="h-8 w-8 text-indigo-400" />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">{user?.username}</h2>
                        <div className="flex items-center gap-2 mt-1">
                            <Shield className="h-4 w-4 text-emerald-400" />
                            <span className="text-sm text-slate-400 font-mono uppercase bg-white/5 px-2 py-0.5 rounded">
                                {user?.access_level} ACCESS
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Change Password Card */}
            <div className="bg-slate-900/40 border border-white/5 rounded-xl p-6 backdrop-blur-sm">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Key className="h-5 w-5 text-slate-400" />
                    Change Password
                </h3>

                <form onSubmit={handleSubmit} className="max-w-md space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Current Password</label>
                        <input
                            type="password"
                            value={passwordData.current_password}
                            onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                            className="w-full px-3 py-2 bg-slate-950/50 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">New Password</label>
                        <input
                            type="password"
                            value={passwordData.new_password}
                            onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                            className="w-full px-3 py-2 bg-slate-950/50 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                            required
                            minLength={8}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Confirm New Password</label>
                        <input
                            type="password"
                            value={passwordData.confirm_password}
                            onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                            className="w-full px-3 py-2 bg-slate-950/50 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                            required
                            minLength={8}
                        />
                    </div>

                    <div className="pt-2">
                        <Button type="submit" isLoading={changePasswordMutation.isPending}>
                            Update Password
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
