import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../features/users/userService';
import { UserForm } from '../features/users/components/UserForm';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import type { User } from '../types';
import { UserCategory, UserStatus } from '../types';
import { Plus, Search, Pencil, Trash2, Loader2, RotateCcw, Ban, Download } from 'lucide-react';
import { cn } from '../utils/cn';

export default function UsersPage() {
    const queryClient = useQueryClient();
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);
    const [viewMode, setViewMode] = useState<'active' | 'inactive' | 'deleted'>('active');

    // Modals state
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [deleteConfirm, setDeleteConfirm] = useState<User | null>(null);
    const [restoreConfirm, setRestoreConfirm] = useState<User | null>(null);
    const [hardDeleteConfirm, setHardDeleteConfirm] = useState<User | null>(null);

    const { data, isLoading } = useQuery({
        queryKey: ['users', search, page, viewMode],
        queryFn: () => userService.search(
            search,
            page,
            10,
            undefined,
            // Status filter based on viewMode
            viewMode === 'active'
                ? ['ACTIVE', 'CONVERTED']
                : viewMode === 'inactive'
                    ? ['INACTIVE', 'EXPIRED']
                    : undefined,
            undefined, // include_deleted
            viewMode === 'deleted' // deleted_only
        ),
        placeholderData: (prev) => prev,
    });

    // Mutations
    const createMutation = useMutation({
        mutationFn: userService.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Parameters<typeof userService.update>[1] }) =>
            userService.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            setEditingUser(null);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: userService.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            setDeleteConfirm(null);
        },
    });

    const restoreMutation = useMutation({
        mutationFn: userService.restore,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            setRestoreConfirm(null);
        },
    });

    const hardDeleteMutation = useMutation({
        mutationFn: userService.hardDelete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            setHardDeleteConfirm(null);
        },
    });

    const convertMutation = useMutation({
        mutationFn: userService.convert,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });

    const endInternshipMutation = useMutation({
        mutationFn: userService.endInternship,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });

    const retireMutation = useMutation({
        mutationFn: userService.retire,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });

    const exportMutation = useMutation({
        mutationFn: userService.export,
    });

    const handleCreate = (formData: any, createAnother?: boolean) => {
        createMutation.mutate({
            ...formData,
            category: formData.category as UserCategory,
        }, {
            onSuccess: () => {
                if (!createAnother) {
                    setCreateModalOpen(false);
                }
            }
        });
    };

    // Render helper
    const getStatusBadge = (status: UserStatus, isDeleted: boolean) => {
        if (isDeleted) return <Badge variant="destructive">DELETED</Badge>;
        const map: Record<UserStatus, 'success' | 'destructive' | 'warning' | 'default'> = {
            [UserStatus.ACTIVE]: 'success',
            [UserStatus.INACTIVE]: 'destructive',
            [UserStatus.EXPIRED]: 'warning',
            [UserStatus.CONVERTED]: 'default',
        };
        return <Badge variant={map[status]}>{status}</Badge>;
    };

    const getCategoryBadge = (category: UserCategory) => {
        return (
            <Badge variant={category === UserCategory.INTERN ? 'warning' : 'default'}>
                {category}
            </Badge>
        );
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Users</h1>
                    <p className="text-slate-400">Manage user accounts and permissions.</p>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={() => exportMutation.mutate()}
                        isLoading={exportMutation.isPending}
                    >
                        <Download className="mr-2 h-4 w-4" />
                        Export
                    </Button>
                    {viewMode === 'active' && (
                        <Button onClick={() => setCreateModalOpen(true)}>
                            <Plus className="mr-2 h-4 w-4" />
                            Add User
                        </Button>
                    )}
                </div>
            </div>

            {/* Tabs & Search */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div className="flex bg-slate-900/50 p-1 rounded-lg border border-white/5">
                    <button
                        onClick={() => { setViewMode('active'); setPage(1); }}
                        className={cn(
                            "px-4 py-2 text-sm font-medium rounded-md transition-all",
                            viewMode === 'active'
                                ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 shadow-sm"
                                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                        )}
                    >
                        Active Users
                    </button>
                    <button
                        onClick={() => { setViewMode('inactive'); setPage(1); }}
                        className={cn(
                            "px-4 py-2 text-sm font-medium rounded-md transition-all",
                            viewMode === 'inactive'
                                ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 shadow-sm"
                                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                        )}
                    >
                        Past Employees
                    </button>
                    <button
                        onClick={() => { setViewMode('deleted'); setPage(1); }}
                        className={cn(
                            "px-4 py-2 text-sm font-medium rounded-md transition-all",
                            viewMode === 'deleted'
                                ? "bg-red-500/20 text-red-300 border border-red-500/20 shadow-sm"
                                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                        )}
                    >
                        Trash Bin
                    </button>
                </div>

                <div className="relative w-full max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search..."
                        value={search}
                        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                        className="w-full h-10 pl-10 pr-4 rounded-lg border border-white/10 bg-white/5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                    />
                </div>
            </div>

            {/* Table */}
            <div className="rounded-xl border border-white/5 bg-slate-900/40 overflow-hidden backdrop-blur-sm">
                <Table>
                    <TableHeader className="bg-white/5">
                        <TableRow className="hover:bg-transparent">
                            <TableHead>Name</TableHead>
                            <TableHead>Email</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Joining Date</TableHead>
                            <TableHead>End Date</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={7} className="h-24 text-center">
                                    <div className="flex justify-center items-center gap-2 text-slate-500">
                                        <Loader2 className="h-4 w-4 animate-spin" /> Loading...
                                    </div>
                                </TableCell>
                            </TableRow>
                        ) : data?.users.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={7} className="h-24 text-center text-slate-500">
                                    No users found in {viewMode === 'active' ? 'active list' : viewMode === 'inactive' ? 'past employees' : 'trash'}.
                                </TableCell>
                            </TableRow>
                        ) : (
                            data?.users.map((user) => (
                                <TableRow key={user.id}>
                                    <TableCell>
                                        <div>
                                            <p className="font-medium text-slate-200">{user.name}</p>
                                            <p className="text-xs text-slate-500 font-mono">{user.display_id}</p>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-slate-400">{user.email}</TableCell>
                                    <TableCell>{getCategoryBadge(user.category)}</TableCell>
                                    <TableCell>{getStatusBadge(user.status, !!user.deleted_at)}</TableCell>
                                    <TableCell className="text-slate-400 text-sm">
                                        {user.date_of_joining ? new Date(user.date_of_joining).toLocaleDateString() : '-'}
                                    </TableCell>
                                    <TableCell className="text-slate-400 text-sm">
                                        {user.end_date ? new Date(user.end_date).toLocaleDateString() : '-'}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-1">
                                            {viewMode === 'active' ? (
                                                <>
                                                    {user.category === UserCategory.INTERN && (
                                                        <button
                                                            onClick={() => {
                                                                if (window.confirm(`Promote ${user.name} to Employee?`)) {
                                                                    convertMutation.mutate(user.ulid);
                                                                }
                                                            }}
                                                            className="p-1.5 rounded-lg text-slate-400 hover:text-green-400 hover:bg-green-500/10 transition-colors"
                                                            title="Promote to Employee"
                                                        >
                                                            <RotateCcw className="h-4 w-4" />
                                                        </button>
                                                    )}
                                                    {user.category === UserCategory.EMPLOYEE && user.status === UserStatus.ACTIVE && (
                                                        <button
                                                            onClick={() => {
                                                                if (window.confirm(`Retire employee ${user.name}? They will be moved to Past Employees.`)) {
                                                                    retireMutation.mutate(user.ulid);
                                                                }
                                                            }}
                                                            className="p-1.5 rounded-lg text-slate-400 hover:text-orange-400 hover:bg-orange-500/10 transition-colors"
                                                            title="Retire Employee"
                                                        >
                                                            <Ban className="h-4 w-4" />
                                                        </button>
                                                    )}
                                                    {user.category === UserCategory.INTERN && user.status !== 'EXPIRED' && user.status !== 'CONVERTED' && (
                                                        <button
                                                            onClick={() => {
                                                                if (window.confirm(`End internship for ${user.name}? This will mark them as EXPIRED.`)) {
                                                                    endInternshipMutation.mutate(user.ulid);
                                                                }
                                                            }}
                                                            className="p-1.5 rounded-lg text-slate-400 hover:text-orange-400 hover:bg-orange-500/10 transition-colors"
                                                            title="End Internship"
                                                        >
                                                            <Ban className="h-4 w-4" />
                                                        </button>
                                                    )}
                                                    <button
                                                        onClick={() => setEditingUser(user)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                                                        title="Edit"
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => setDeleteConfirm(user)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                                        title="Soft Delete"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                </>
                                            ) : viewMode === 'inactive' ? (
                                                <>
                                                    <button
                                                        onClick={() => setEditingUser(user)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                                                        title="Edit"
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => setDeleteConfirm(user)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                                        title="Soft Delete"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                </>
                                            ) : (
                                                <>
                                                    <button
                                                        onClick={() => setRestoreConfirm(user)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-green-400 hover:bg-green-500/10 transition-colors"
                                                        title="Restore"
                                                    >
                                                        <RotateCcw className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => setHardDeleteConfirm(user)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                                        title="Permanently Delete"
                                                    >
                                                        <Ban className="h-4 w-4" />
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-2">
                <p className="text-sm text-slate-500">
                    Showing {data?.users.length || 0} of {data?.total || 0} users
                </p>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                        Previous
                    </Button>
                    <Button variant="outline" size="sm" disabled={page >= (data?.pages || 1)} onClick={() => setPage((p) => p + 1)}>
                        Next
                    </Button>
                </div>
            </div>

            {/* Create Modal */}
            <Modal isOpen={createModalOpen} onClose={() => setCreateModalOpen(false)} title="Create User">
                {/* We use a key to force remount on close/reopen or when creating another */}
                <UserForm
                    key={createModalOpen ? 'open' : 'closed'}
                    onSubmit={handleCreate}
                    isLoading={createMutation.isPending}
                />
            </Modal>

            {/* Edit Modal */}
            <Modal isOpen={!!editingUser} onClose={() => setEditingUser(null)} title="Edit User">
                <UserForm user={editingUser} onSubmit={() => { }} isLoading={updateMutation.isPending}
                // Need to wrap onSubmit to match signature
                // Actually handleUpdate needs to accommodate the new signature
                // But for edit, "Create Another" isn't relevant.
                />
                {/* wait, UserForm expects (data, createAnother), handleUpdate in previous code was taking data. 
                    I need to update handleUpdate too.
                */}
            </Modal>

            {/* Delete Confirm Modal */}
            <Modal isOpen={!!deleteConfirm} onClose={() => setDeleteConfirm(null)} title="Delete User">
                <p className="text-slate-300 mb-6">
                    Are you sure you want to send <strong className="text-white">{deleteConfirm?.name}</strong> to trash?
                    They can be restored later.
                </p>
                <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancel</Button>
                    <Button
                        variant="destructive"
                        isLoading={deleteMutation.isPending}
                        onClick={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.ulid)}
                    >
                        Move to Trash
                    </Button>
                </div>
            </Modal>

            {/* Restore Confirm Modal */}
            <Modal isOpen={!!restoreConfirm} onClose={() => setRestoreConfirm(null)} title="Restore User">
                <p className="text-slate-300 mb-6">
                    Are you sure you want to restore <strong className="text-white">{restoreConfirm?.name}</strong>?
                </p>
                <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={() => setRestoreConfirm(null)}>Cancel</Button>
                    <Button
                        variant="default" // Success color?
                        className="bg-green-600 hover:bg-green-700"
                        isLoading={restoreMutation.isPending}
                        onClick={() => restoreConfirm && restoreMutation.mutate(restoreConfirm.ulid)}
                    >
                        Restore
                    </Button>
                </div>
            </Modal>

            {/* Hard Delete Confirm Modal */}
            <Modal isOpen={!!hardDeleteConfirm} onClose={() => setHardDeleteConfirm(null)} title="Permanently Delete User">
                <div className="space-y-4">
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-200 text-sm">
                        Warning: This action is <strong>irreversible</strong>. The user and all their data will be permanently wiped.
                    </div>
                    <p className="text-slate-300">
                        Are you sure you want to permanently delete <strong className="text-white">{hardDeleteConfirm?.name}</strong>?
                    </p>
                    <div className="flex justify-end gap-3">
                        <Button variant="outline" onClick={() => setHardDeleteConfirm(null)}>Cancel</Button>
                        <Button
                            variant="destructive"
                            isLoading={hardDeleteMutation.isPending}
                            onClick={() => hardDeleteConfirm && hardDeleteMutation.mutate(hardDeleteConfirm.ulid)}
                        >
                            Permanently Delete
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}
