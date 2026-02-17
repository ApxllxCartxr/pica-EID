import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditService } from '../features/audit/auditService';
import { Button } from '../components/ui/Button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { Loader2, Download, FileText } from 'lucide-react';

export default function AuditPage() {
    const [page, setPage] = useState(1);

    const { data, isLoading } = useQuery({
        queryKey: ['audit-logs', page],
        queryFn: () => auditService.getAll(page, 20),
        placeholderData: (prev) => prev,
    });

    const handleExport = async () => {
        try {
            await auditService.export();
        } catch {
            alert('Failed to export audit logs.');
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Audit Logs</h1>
                    <p className="text-slate-400">Track system activity and user actions.</p>
                </div>
                <Button variant="outline" onClick={handleExport}>
                    <Download className="mr-2 h-4 w-4" />
                    Export CSV
                </Button>
            </div>

            <div className="rounded-xl border border-white/5 bg-slate-900/40 overflow-hidden backdrop-blur-sm">
                <Table>
                    <TableHeader className="bg-white/5">
                        <TableRow className="hover:bg-transparent">
                            <TableHead>Timestamp</TableHead>
                            <TableHead>User</TableHead>
                            <TableHead>Action</TableHead>
                            <TableHead>Resource</TableHead>
                            <TableHead>Details</TableHead>
                            <TableHead>IP Address</TableHead>
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
                        ) : data?.logs.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} className="h-24 text-center text-slate-500">No logs found.</TableCell>
                            </TableRow>
                        ) : (
                            data?.logs.map((log) => (
                                <TableRow key={log.id}>
                                    <TableCell className="font-mono text-xs text-slate-400 whitespace-nowrap">
                                        {new Date(log.timestamp).toLocaleString()}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-col">
                                            <span className="font-medium text-slate-200">{log.changed_by_name || "System"}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="outline" className="border-indigo-500/20 text-indigo-400">{log.action}</Badge>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <FileText className="h-3 w-3 text-slate-500" />
                                            <span className="text-slate-300">{log.entity_type}</span>
                                            {log.entity_id && <span className="text-xs text-slate-500">#{log.entity_id}</span>}
                                        </div>
                                    </TableCell>
                                    <TableCell className="max-w-xs truncate text-xs font-mono text-slate-500">
                                        {log.description || JSON.stringify(log.new_value || {})}
                                    </TableCell>
                                    <TableCell className="text-slate-500 text-xs font-mono">{log.ip_address || '-'}</TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>

            <div className="flex items-center justify-between px-2">
                <p className="text-sm text-slate-500">
                    Showing {data?.logs.length || 0} of {data?.total || 0} entries
                </p>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1 || isLoading} onClick={() => setPage((p) => p - 1)}>Previous</Button>
                    <Button variant="outline" size="sm" disabled={page >= (data?.pages || 1) || isLoading} onClick={() => setPage((p) => p + 1)}>Next</Button>
                </div>
            </div>
        </div>
    );
}
