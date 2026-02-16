import { type HTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const badgeVariants = cva(
    'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium transition-colors',
    {
        variants: {
            variant: {
                default: 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20',
                secondary: 'bg-secondary text-secondary-foreground',
                destructive: 'bg-red-500/10 text-red-400 border border-red-500/20',
                success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
                warning: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
                outline: 'border border-white/10 text-slate-300',
            },
        },
        defaultVariants: {
            variant: 'default',
        },
    }
);

export interface BadgeProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> { }

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
    ({ className, variant, ...props }, ref) => {
        return (
            <div ref={ref} className={cn(badgeVariants({ variant }), className)} {...props} />
        );
    }
);
Badge.displayName = 'Badge';

export { Badge, badgeVariants };
