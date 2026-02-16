import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { roleService } from '../features/roles/roleService';
import { RoleForm } from '../features/roles/components/RoleForm';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import type { Role } from '../types';
import { Plus, Pencil, Trash2, Loader2, RefreshCw } from 'lucide-react';

export default function RolesPage() {
    const queryClient = useQueryClient();
    const [page, setPage] = useState(1);
    const [activeTab, setActiveTab] = useState<'active' | 'trash'>('active');
    const [modalOpen, setModalOpen] = useState(false);
    const [editingRole, setEditingRole] = useState<Role | null>(null);
    const [deleteConfirm, setDeleteConfirm] = useState<Role | null>(null);
    const [restoreConfirm, setRestoreConfirm] = useState<Role | null>(null);
    const [hardDeleteConfirm, setHardDeleteConfirm] = useState<Role | null>(null);

    const { data, isLoading } = useQuery({
        queryKey: ['roles', page, activeTab],
        queryFn: () => roleService.getAll(page, 20, false, activeTab === 'trash'),
        placeholderData: (prev) => prev,
    });

    const createMutation = useMutation({
        mutationFn: roleService.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            setModalOpen(false);
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Parameters<typeof roleService.update>[1] }) =>
            roleService.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            setEditingRole(null);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: roleService.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            setDeleteConfirm(null);
        },
    });

    const restoreMutation = useMutation({
        mutationFn: roleService.restore,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            setRestoreConfirm(null);
        },
    });

    const hardDeleteMutation = useMutation({
        mutationFn: roleService.hardDelete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['roles'] });
            setHardDeleteConfirm(null);
        },
    });

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Roles</h1>
                    <p className="text-slate-400">Manage system roles and permissions.</p>
                </div>
                {activeTab === 'active' && (
                    <Button onClick={() => setModalOpen(true)}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Role
                    </Button>
                )}
            </div>

            {/* Tabs */}
            <div className="flex border-b border-white/10">
                <button
                    onClick={() => { setActiveTab('active'); setPage(1); }}
                    className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'active'
                        ? 'border-indigo-500 text-indigo-400'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                        }`}
                >
                    Active Roles
                </button>
                <button
                    onClick={() => { setActiveTab('trash'); setPage(1); }}
                    className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'trash'
                        ? 'border-indigo-500 text-indigo-400'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                        }`}
                >
                    Trash Bin
                </button>
            </div>

            <div className="rounded-xl border border-white/5 bg-slate-900/40 overflow-hidden backdrop-blur-sm">
                <Table>
                    <TableHeader className="bg-white/5">
                        <TableRow className="hover:bg-transparent">
                            <TableHead>Name</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead>Clearance</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Assigned</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={6} className="h-24 text-center">
                                    <div className="flex justify-center items-center gap-2 text-slate-500">
                                        <Loader2 className="h-4 w-4 animate-spin" /> Loading...
                                    </div>
                                </TableCell>
                            </TableRow>
                        ) : data?.roles.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} className="h-24 text-center text-slate-500">
                                    No roles found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            data?.roles.map((role) => (
                                <TableRow key={role.id}>
                                    <TableCell className="font-medium text-slate-200">{role.name}</TableCell>
                                    <TableCell className="text-slate-400 max-w-xs truncate">{role.description || '-'}</TableCell>
                                    <TableCell>
                                        <Badge variant="outline">{role.clearance_level}</Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={role.is_active ? 'success' : 'destructive'}>
                                            {role.is_active ? 'Active' : 'Inactive'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-slate-400">{role.assigned_users_count} users</TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-1">
                                            {activeTab === 'active' ? (
                                                <>
                                                    <button
                                                        onClick={() => setEditingRole(role)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                                                        title="Edit"
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => setDeleteConfirm(role)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                                        title="Soft Delete"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                </>
                                            ) : (
                                                <>
                                                    <button
                                                        onClick={() => setRestoreConfirm(role)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                                                        title="Restore"
                                                    >
                                                        <RefreshCw className="h-4 w-4" /> {/* Need to import RefreshCw or Undo */}
                                                    </button>
                                                    <button
                                                        onClick={() => setHardDeleteConfirm(role)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                                        title="Permanently Delete"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
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

            <div className="flex items-center justify-between px-2">
                <p className="text-sm text-slate-500">
                    Showing {data?.roles.length || 0} of {data?.total || 0} roles
                </p>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</Button>
                    <Button variant="outline" size="sm" disabled={page >= (data?.pages || 1)} onClick={() => setPage((p) => p + 1)}>Next</Button>
                </div>
            </div>

            <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Create Role">
                <RoleForm onSubmit={(d) => createMutation.mutate(d)} isLoading={createMutation.isPending} />
            </Modal>

            <Modal isOpen={!!editingRole} onClose={() => setEditingRole(null)} title="Edit Role">
                <RoleForm role={editingRole} onSubmit={(d) => editingRole && updateMutation.mutate({ id: editingRole.id, data: d })} isLoading={updateMutation.isPending} />
            </Modal>

            <Modal isOpen={!!deleteConfirm} onClose={() => setDeleteConfirm(null)} title="Delete Role">
                <p className="text-slate-300 mb-6">
                    Are you sure you want to move role <strong className="text-white">{deleteConfirm?.name}</strong> to trash?
                </p>
                <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancel</Button>
                    <Button variant="destructive" isLoading={deleteMutation.isPending} onClick={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.id)}>
                        Move to Trash
                    </Button>
                </div>
            </Modal>

            <Modal isOpen={!!restoreConfirm} onClose={() => setRestoreConfirm(null)} title="Restore Role">
                <p className="text-slate-300 mb-6">
                    Are you sure you want to restore role <strong className="text-white">{restoreConfirm?.name}</strong>?
                </p>
                <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={() => setRestoreConfirm(null)}>Cancel</Button>
                    <Button onClick={() => restoreConfirm && restoreMutation.mutate(restoreConfirm.id)} isLoading={restoreMutation.isPending}>
                        Restore
                    </Button>
                </div>
            </Modal>

            <Modal isOpen={!!hardDeleteConfirm} onClose={() => setHardDeleteConfirm(null)} title="Permanently Delete Role">
                <p className="text-slate-300 mb-6">
                    Are you sure you want to <strong className="text-red-400">permanently delete</strong> role <strong className="text-white">{hardDeleteConfirm?.name}</strong>?
                    <br /><br />
                    <span className="text-sm text-slate-400">This action cannot be undone.</span>
                </p>
                <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={() => setHardDeleteConfirm(null)}>Cancel</Button>
                    <Button variant="destructive" isLoading={hardDeleteMutation.isPending} onClick={() => hardDeleteConfirm && hardDeleteMutation.mutate(hardDeleteConfirm.id)}>
                        Permanently Delete
                    </Button>
                </div>
            </Modal>
        </div>
    );
}
