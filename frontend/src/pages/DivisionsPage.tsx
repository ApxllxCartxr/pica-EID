import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { divisionService } from '../features/divisions/divisionService';
import { DivisionForm } from '../features/divisions/components/DivisionForm';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import type { Division } from '../types';
import { Plus, Trash2, Loader2, RefreshCw, Pencil } from 'lucide-react';

export default function DivisionsPage() {
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<'active' | 'trash'>('active');
    const [modalOpen, setModalOpen] = useState(false);
    const [editingDivision, setEditingDivision] = useState<Division | null>(null);
    const [deleteConfirm, setDeleteConfirm] = useState<Division | null>(null);
    const [restoreConfirm, setRestoreConfirm] = useState<Division | null>(null);
    const [hardDeleteConfirm, setHardDeleteConfirm] = useState<Division | null>(null);

    const { data: divisions, isLoading } = useQuery({
        queryKey: ['divisions', activeTab],
        queryFn: () => divisionService.getAll(false, activeTab === 'trash'),
        placeholderData: (prev) => prev,
    });

    const createMutation = useMutation({
        mutationFn: divisionService.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['divisions'] });
            setModalOpen(false);
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<Division> }) =>
            divisionService.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['divisions'] });
            setEditingDivision(null);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: divisionService.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['divisions'] });
            setDeleteConfirm(null);
        },
    });

    const restoreMutation = useMutation({
        mutationFn: divisionService.restore,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['divisions'] });
            setRestoreConfirm(null);
        },
    });

    const hardDeleteMutation = useMutation({
        mutationFn: divisionService.hardDelete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['divisions'] });
            setHardDeleteConfirm(null);
        },
    });

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Domains</h1>
                    <p className="text-slate-400">Manage business domains.</p>
                </div>
                {activeTab === 'active' && (
                    <Button onClick={() => setModalOpen(true)}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Domain
                    </Button>
                )}
            </div>

            {/* Tabs */}
            <div className="flex border-b border-white/10">
                <button
                    onClick={() => setActiveTab('active')}
                    className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${activeTab === 'active'
                        ? 'border-indigo-500 text-indigo-400'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                        }`}
                >
                    Active Domains
                </button>
                <button
                    onClick={() => setActiveTab('trash')}
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
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={4} className="h-24 text-center">
                                    <div className="flex justify-center items-center gap-2 text-slate-500">
                                        <Loader2 className="h-4 w-4 animate-spin" /> Loading...
                                    </div>
                                </TableCell>
                            </TableRow>
                        ) : divisions?.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="h-24 text-center text-slate-500">
                                    No domains found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            divisions?.map((division) => (
                                <TableRow key={division.id}>
                                    <TableCell className="font-medium text-slate-200">{division.name}</TableCell>
                                    <TableCell className="text-slate-400 max-w-xs truncate">{division.description || '-'}</TableCell>
                                    <TableCell>
                                        <Badge variant={division.is_active ? 'success' : 'destructive'}>
                                            {division.is_active ? 'Active' : 'Inactive'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-1">
                                            {activeTab === 'active' ? (
                                                <>
                                                    <button
                                                        onClick={() => setEditingDivision(division)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                                                        title="Edit"
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => setDeleteConfirm(division)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                                        title="Soft Delete"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                </>
                                            ) : (
                                                <>
                                                    <button
                                                        onClick={() => setRestoreConfirm(division)}
                                                        className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                                                        title="Restore"
                                                    >
                                                        <RefreshCw className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => setHardDeleteConfirm(division)}
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

            <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Create Domain">
                <DivisionForm onSubmit={(d) => createMutation.mutate(d)} isLoading={createMutation.isPending} />
            </Modal>

            <Modal isOpen={!!editingDivision} onClose={() => setEditingDivision(null)} title="Edit Domain">
                <DivisionForm
                    division={editingDivision}
                    onSubmit={(d) => editingDivision && updateMutation.mutate({ id: editingDivision.id, data: d })}
                    isLoading={updateMutation.isPending}
                />
            </Modal>

            <Modal isOpen={!!deleteConfirm} onClose={() => setDeleteConfirm(null)} title="Delete Domain">
                <p className="text-slate-300 mb-6">
                    Are you sure you want to move domain <strong className="text-white">{deleteConfirm?.name}</strong> to trash?
                </p>
                <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancel</Button>
                    <Button variant="destructive" isLoading={deleteMutation.isPending} onClick={() => deleteConfirm && deleteMutation.mutate(deleteConfirm.id)}>
                        Move to Trash
                    </Button>
                </div>
            </Modal>

            <Modal isOpen={!!restoreConfirm} onClose={() => setRestoreConfirm(null)} title="Restore Domain">
                <p className="text-slate-300 mb-6">
                    Are you sure you want to restore domain <strong className="text-white">{restoreConfirm?.name}</strong>?
                </p>
                <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={() => setRestoreConfirm(null)}>Cancel</Button>
                    <Button onClick={() => restoreConfirm && restoreMutation.mutate(restoreConfirm.id)} isLoading={restoreMutation.isPending}>
                        Restore
                    </Button>
                </div>
            </Modal>

            <Modal isOpen={!!hardDeleteConfirm} onClose={() => setHardDeleteConfirm(null)} title="Permanently Delete Domain">
                <p className="text-slate-300 mb-6">
                    Are you sure you want to <strong className="text-red-400">permanently delete</strong> domain <strong className="text-white">{hardDeleteConfirm?.name}</strong>?
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
