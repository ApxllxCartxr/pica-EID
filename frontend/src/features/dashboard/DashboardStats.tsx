import { useQuery } from '@tanstack/react-query';
import { dashboardService } from './dashboardService';
import { BentoStatCard } from './BentoStatCard';
import { Users, UserCheck, Shield, Activity, Loader2 } from 'lucide-react';

export function DashboardStats() {
    const { data, isLoading } = useQuery({
        queryKey: ['dashboard-stats'],
        queryFn: dashboardService.getStats,
    });

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-48">
                <Loader2 className="h-6 w-6 text-indigo-400 animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Main Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <BentoStatCard
                    title="Total Users"
                    value={data?.total_users ?? 0}
                    icon={<Users className="h-5 w-5" />}
                    description="All registered users"
                    trend={12}
                />
                <BentoStatCard
                    title="Active Users"
                    value={data?.active_users ?? 0}
                    icon={<UserCheck className="h-5 w-5" />}
                    description="Currently active"
                    trend={5}
                />
                <BentoStatCard
                    title="Interns"
                    value={data?.total_interns ?? 0}
                    icon={<Activity className="h-5 w-5" />}
                    description="Active interns"
                />
                <BentoStatCard
                    title="Total Roles"
                    value={data?.total_roles ?? 0}
                    icon={<Shield className="h-5 w-5" />}
                    description="System roles"
                />
            </div>

            {/* Recent Activity */}
            {data?.recent_actions && data.recent_actions.length > 0 && (
                <div className="rounded-xl border border-white/5 bg-slate-900/40 backdrop-blur-sm p-6">
                    <h3 className="text-sm font-medium text-slate-400 mb-4">Recent Activity</h3>
                    <div className="space-y-3">
                        {data.recent_actions.slice(0, 5).map((action, index) => (
                            <div key={index} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                                <div className="flex items-center gap-3">
                                    <div className="h-2 w-2 rounded-full bg-indigo-400" />
                                    <span className="text-sm text-slate-300">{action.action}</span>
                                    <span className="text-xs text-slate-500">{action.entity_type}</span>
                                </div>
                                <span className="text-xs text-slate-500 font-mono">
                                    {new Date(action.timestamp).toLocaleString()}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
