import { useQueryClient } from '@tanstack/react-query';
import { DashboardStats } from '../features/dashboard/DashboardStats';
import { Button } from '../components/ui/Button';
import { RefreshCw } from 'lucide-react';

export default function DashboardPage() {
    const queryClient = useQueryClient();

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Overview</h1>
                    <p className="text-slate-400">System metrics and recent activity.</p>
                </div>
                <Button
                    variant="outline"
                    onClick={() => queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })}
                >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>
            <DashboardStats />
        </div>
    );
}
