import type { ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface BentoStatCardProps {
    title: string;
    value: string | number;
    icon?: ReactNode;
    description?: string;
    trend?: number;
    className?: string;
}

export function BentoStatCard({ title, value, icon, description, trend, className }: BentoStatCardProps) {
    return (
        <div
            className={cn(
                'group relative rounded-xl border border-white/5 bg-slate-900/40 backdrop-blur-sm p-6 transition-all duration-300 hover:bg-slate-900/60 hover:border-white/10 hover:shadow-lg hover:shadow-indigo-500/5',
                className
            )}
        >
            <div className="flex items-start justify-between">
                <div className="space-y-2">
                    <p className="text-sm font-medium text-slate-400">{title}</p>
                    <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
                    {description && (
                        <p className="text-xs text-slate-500">{description}</p>
                    )}
                </div>
                {icon && (
                    <div className="rounded-lg bg-indigo-500/10 p-2.5 text-indigo-400 group-hover:bg-indigo-500/20 transition-colors">
                        {icon}
                    </div>
                )}
            </div>
            {trend !== undefined && (
                <div className={`mt-3 flex items-center gap-1 text-xs font-medium ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {trend >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    <span>{Math.abs(trend)}% from last month</span>
                </div>
            )}
        </div>
    );
}
