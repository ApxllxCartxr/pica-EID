import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import type { Domain } from '../../../types';

const domainSchema = z.object({
    name: z.string().min(1, 'Division name is required'),
    description: z.string().optional(),
    is_active: z.boolean(),
});

type DomainFormData = z.infer<typeof domainSchema>;

interface DomainFormProps {
    domain?: Domain | null;
    onSubmit: (data: DomainFormData) => void;
    isLoading?: boolean;
}

export function DomainForm({ domain, onSubmit, isLoading }: DomainFormProps) {
    const { register, handleSubmit, formState: { errors } } = useForm<DomainFormData>({
        resolver: zodResolver(domainSchema) as any,
        defaultValues: {
            name: domain?.name || '',
            description: domain?.description || '',
            is_active: domain?.is_active ?? true,
        },
    });

    return (
        <form onSubmit={handleSubmit((data) => onSubmit(data))} className="space-y-4">
            <Input
                id="domain-name"
                label="Division Name"
                placeholder="e.g. North America"
                error={errors.name?.message}
                {...register('name')}
            />
            <Input
                id="domain-description"
                label="Description"
                placeholder="Brief description"
                error={errors.description?.message}
                {...register('description')}
            />
            <div className="flex items-center gap-3">
                <input
                    type="checkbox"
                    id="is-active"
                    {...register('is_active')}
                    className="h-4 w-4 rounded border-white/10 bg-white/5 text-indigo-600 focus:ring-indigo-500/50"
                />
                <label htmlFor="is-active" className="text-sm font-medium text-slate-300">
                    Active
                </label>
            </div>
            <div className="flex justify-end gap-3 pt-4">
                <Button type="submit" isLoading={isLoading}>
                    {domain ? 'Update Division' : 'Create Division'}
                </Button>
            </div>
        </form>
    );
}
