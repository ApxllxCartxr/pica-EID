import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import type { Role } from '../../../types';

const roleSchema = z.object({
    name: z.string().min(1, 'Role name is required'),
    description: z.string().optional(),
    clearance_level: z.coerce.number().min(0).max(10),
    is_active: z.boolean(),
});

type RoleFormData = z.infer<typeof roleSchema>;

interface RoleFormProps {
    role?: Role | null;
    onSubmit: (data: RoleFormData) => void;
    isLoading?: boolean;
}

export function RoleForm({ role, onSubmit, isLoading }: RoleFormProps) {
    const { register, handleSubmit, formState: { errors } } = useForm<RoleFormData>({
        resolver: zodResolver(roleSchema) as any,
        defaultValues: {
            name: role?.name || '',
            description: role?.description || '',
            clearance_level: role?.clearance_level ?? 1,
            is_active: role?.is_active ?? true,
        },
    });

    return (
        <form onSubmit={handleSubmit((data) => onSubmit(data))} className="space-y-4">
            <Input
                id="role-name"
                label="Role Name"
                placeholder="e.g. Manager"
                error={errors.name?.message}
                {...register('name')}
            />
            <Input
                id="role-description"
                label="Description"
                placeholder="Brief description"
                error={errors.description?.message}
                {...register('description')}
            />
            <Input
                id="clearance-level"
                type="number"
                label="Clearance Level (0-10)"
                error={errors.clearance_level?.message}
                {...register('clearance_level')}
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
                    {role ? 'Update Role' : 'Create Role'}
                </Button>
            </div>
        </form>
    );
}
