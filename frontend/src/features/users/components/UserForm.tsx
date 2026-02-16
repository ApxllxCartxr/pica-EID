import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery } from '@tanstack/react-query';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import type { User } from '../../../types';
import { UserCategory } from '../../../types';
import { domainService } from '../../domains/domainService';
import { divisionService } from '../../divisions/divisionService';
import { roleService } from '../../roles/roleService';

const userSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    email: z.string().email('Invalid email address'),
    phone_number: z.string().optional(),
    category: z.nativeEnum(UserCategory),
    start_date: z.string().optional(),
    end_date: z.string().optional(),
    date_of_joining: z.string().optional(),
    domain_id: z.coerce.number().optional(),
    division_id: z.coerce.number().optional(),
    role_ids: z.array(z.number()).optional(),
}).superRefine((data, ctx) => {
    if (data.category === UserCategory.INTERN) {
        if (!data.start_date) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: "Start date is required for interns",
                path: ["start_date"]
            });
        }
        if (!data.end_date) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: "End date is required for interns",
                path: ["end_date"]
            });
        }
    }
});

type UserFormData = z.infer<typeof userSchema>;

interface UserFormProps {
    user?: User | null;
    onSubmit: (data: UserFormData, createAnother?: boolean) => void;
    isLoading?: boolean;
}

export function UserForm({ user, onSubmit, isLoading }: UserFormProps) {
    const { register, handleSubmit, watch, control, formState: { errors } } = useForm<UserFormData>({
        resolver: zodResolver(userSchema) as any,
        defaultValues: {
            name: user?.name || '',
            email: user?.email || '',
            phone_number: user?.phone_number || '',
            category: user?.category || UserCategory.EMPLOYEE,
            start_date: user?.start_date ? new Date(user.start_date).toISOString().split('T')[0] : '',
            end_date: user?.end_date ? new Date(user.end_date).toISOString().split('T')[0] : '',
            date_of_joining: user?.date_of_joining ? new Date(user.date_of_joining).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
            domain_id: user?.domain?.id,
            division_id: user?.division?.id,
            role_ids: user?.user_roles?.map(ur => ur.role.id) || [],
        },
    });

    const category = watch('category');

    // Fetch lists
    const { data: domains } = useQuery({ queryKey: ['domains'], queryFn: () => domainService.getAll() });
    const { data: divisions } = useQuery({ queryKey: ['divisions'], queryFn: () => divisionService.getAll() });
    const { data: roleData } = useQuery({ queryKey: ['roles'], queryFn: () => roleService.getAll(1, 100) });
    const roles = roleData?.roles || [];

    return (
        <form className="space-y-4">
            <Input
                id="name"
                label="Full Name"
                placeholder="John Doe"
                error={errors.name?.message}
                {...register('name')}
            />
            <Input
                id="email"
                type="email"
                label="Email"
                placeholder="john@example.com"
                error={errors.email?.message}
                {...register('email')}
            />
            <div className="grid grid-cols-2 gap-4">
                <Input
                    id="phone_number"
                    label="Phone Number"
                    placeholder="+91..."
                    error={errors.phone_number?.message}
                    {...register('phone_number')}
                />
                <Input
                    id="date_of_joining"
                    type="date"
                    label="Date of Joining"
                    error={errors.date_of_joining?.message}
                    {...register('date_of_joining')}
                />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-300">Domain</label>
                    <select
                        {...register('domain_id')}
                        className="flex h-10 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    >
                        <option value="" className="bg-slate-900">Select Domain</option>
                        {domains?.map((d) => (
                            <option key={d.id} value={d.id} className="bg-slate-900">{d.name}</option>
                        ))}
                    </select>
                </div>
                <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-300">Division</label>
                    <select
                        {...register('division_id')}
                        className="flex h-10 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    >
                        <option value="" className="bg-slate-900">Select Division</option>
                        {divisions?.map((d) => (
                            <option key={d.id} value={d.id} className="bg-slate-900">{d.name}</option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-300">Roles</label>
                <Controller
                    control={control}
                    name="role_ids"
                    render={({ field: { onChange, value } }) => (
                        <div className="grid grid-cols-2 gap-2 p-3 rounded-lg border border-white/10 bg-white/5 max-h-40 overflow-y-auto">
                            {roles.map((role) => (
                                <label key={role.id} className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        value={role.id}
                                        checked={(value || []).includes(role.id)}
                                        onChange={(e) => {
                                            const checked = e.target.checked;
                                            const current = value || [];
                                            if (checked) {
                                                onChange([...current, role.id]);
                                            } else {
                                                onChange(current.filter((id) => id !== role.id));
                                            }
                                        }}
                                        className="rounded border-white/10 bg-slate-900/50 text-indigo-500 focus:ring-indigo-500/50"
                                    />
                                    <span className="text-sm text-slate-300">{role.name}</span>
                                </label>
                            ))}
                        </div>
                    )}
                />
            </div>

            <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-300">Category</label>
                <select
                    {...register('category')}
                    className="flex h-10 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                >
                    <option value={UserCategory.EMPLOYEE} className="bg-slate-900">Employee</option>
                    <option value={UserCategory.INTERN} className="bg-slate-900">Intern</option>
                </select>
                {errors.category && <p className="text-xs text-red-400">{errors.category.message}</p>}
            </div>

            {category === UserCategory.INTERN && (
                <div className="grid grid-cols-2 gap-4">
                    <Input
                        id="start_date"
                        type="date"
                        label="Internship Start"
                        error={errors.start_date?.message}
                        {...register('start_date')}
                    />
                    <Input
                        id="end_date"
                        type="date"
                        label="Internship End"
                        error={errors.end_date?.message}
                        {...register('end_date')}
                    />
                </div>
            )}

            <div className="flex justify-end gap-3 pt-4">
                {!user && (
                    <Button
                        type="button"
                        variant="outline"
                        isLoading={isLoading}
                        onClick={handleSubmit((data) => {
                            const sanitzedData = {
                                ...data,
                                start_date: data.start_date || undefined,
                                end_date: data.end_date || undefined,
                                date_of_joining: data.date_of_joining || undefined,
                                domain_id: data.domain_id || undefined,
                                division_id: data.division_id || undefined,
                            };
                            // @ts-ignore
                            onSubmit(sanitzedData, true);
                        })}
                    >
                        Save & Create Another
                    </Button>
                )}
                <Button
                    type="button"
                    isLoading={isLoading}
                    onClick={handleSubmit((data) => {
                        const sanitzedData = {
                            ...data,
                            start_date: data.start_date || undefined,
                            end_date: data.end_date || undefined,
                            date_of_joining: data.date_of_joining || undefined,
                            domain_id: data.domain_id || undefined,
                            division_id: data.division_id || undefined,
                        };
                        // @ts-ignore
                        onSubmit(sanitzedData, false);
                    })}
                >
                    {user ? 'Update User' : 'Create User'}
                </Button>
            </div>
        </form>
    );
}
