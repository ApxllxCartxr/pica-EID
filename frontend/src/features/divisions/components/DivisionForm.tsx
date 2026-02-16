import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import type { Division } from '../../../types';

const divisionSchema = z.object({
    name: z.string().min(1, 'Division name is required'),
    description: z.string().optional(),
    is_active: z.boolean(),
});

type DivisionFormData = z.infer<typeof divisionSchema>;

interface DivisionFormProps {
    division?: Division | null;
    onSubmit: (data: DivisionFormData) => void;
    isLoading?: boolean;
}

export function DivisionForm({ division, onSubmit, isLoading }: DivisionFormProps) {
    const { register, handleSubmit, formState: { errors } } = useForm<DivisionFormData>({
        resolver: zodResolver(divisionSchema) as any,
        defaultValues: {
            name: division?.name || '',
            description: division?.description || '',
            is_active: division?.is_active ?? true,
        },
    });

    return (
        <form onSubmit={handleSubmit((data) => onSubmit(data))} className="space-y-4">
            <Input
                id="division-name"
                label="Division Name"
                placeholder="e.g. North America"
                error={errors.name?.message}
                {...register('name')}
            />
            <Input
                id="division-description"
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
                    {division ? 'Update Division' : 'Create Division'}
                </Button>
            </div>
        </form>
    );
}
