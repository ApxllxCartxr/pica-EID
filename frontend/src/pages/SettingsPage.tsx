import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { sheetService } from '../features/sheets/sheetService';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { RefreshCw, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';

export default function SettingsPage() {
    const queryClient = useQueryClient();
    const [page, setPage] = useState(1);

    const { data: logsData, isLoading: logsLoading } = useQuery({
        queryKey: ['sync-logs', page],
        queryFn: () => sheetService.getLogs(page, 10),
        placeholderData: (prev) => prev,
        refetchInterval: 5000,
    });

    const syncMutation = useMutation({
        mutationFn: sheetService.sync,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sync-logs'] });
        },
    });

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Settings</h1>
                <p className="text-slate-400">Manage application configuration and integrations.</p>
            </div>

            <div className="grid gap-6">
                <Card className="bg-slate-900/40 border-white/5 backdrop-blur-sm">
                    <CardHeader>
                        <CardTitle>Google Sheets Integration</CardTitle>
                        <CardDescription>Sync user data from the configured Google Sheet.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <p className="font-medium text-slate-200">Manual Sync</p>
                                <p className="text-sm text-slate-400">Trigger a manual synchronization to update user records.</p>
                            </div>
                            <Button onClick={() => syncMutation.mutate()} isLoading={syncMutation.isPending} disabled={syncMutation.isPending}>
                                <RefreshCw className={`mr-2 h-4 w-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                                Sync Now
                            </Button>
                        </div>

                        <div className="mt-8">
                            <h3 className="text-sm font-medium text-slate-200 mb-4">Recent Sync Logs</h3>
                            <div className="rounded-lg border border-white/5 overflow-hidden">
                                <Table>
                                    <TableHeader className="bg-white/5">
                                        <TableRow className="hover:bg-transparent">
                                            <TableHead>Status</TableHead>
                                            <TableHead>Started At</TableHead>
                                            <TableHead>Completed At</TableHead>
                                            <TableHead>Details</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {logsLoading ? (
                                            <TableRow>
                                                <TableCell colSpan={4} className="h-24 text-center">
                                                    <div className="flex justify-center items-center gap-2 text-slate-500">
                                                        <Loader2 className="h-4 w-4 animate-spin" /> Loading...
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        ) : logsData?.logs.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={4} className="h-24 text-center text-slate-500">No logs found.</TableCell>
                                            </TableRow>
                                        ) : (
                                            logsData?.logs.map((log) => (
                                                <TableRow key={log.id}>
                                                    <TableCell>
                                                        {log.status === 'SUCCESS' && (
                                                            <Badge variant="success" className="gap-1 pl-1.5"><CheckCircle className="h-3 w-3" /> Success</Badge>
                                                        )}
                                                        {log.status === 'FAILURE' && (
                                                            <Badge variant="destructive" className="gap-1 pl-1.5"><XCircle className="h-3 w-3" /> Failure</Badge>
                                                        )}
                                                        {log.status === 'IN_PROGRESS' && (
                                                            <Badge variant="warning" className="gap-1 pl-1.5"><Clock className="h-3 w-3 animate-pulse" /> Running</Badge>
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="text-slate-400 text-xs font-mono">{new Date(log.started_at).toLocaleString()}</TableCell>
                                                    <TableCell className="text-slate-400 text-xs font-mono">{log.completed_at ? new Date(log.completed_at).toLocaleString() : '-'}</TableCell>
                                                    <TableCell className="text-slate-500 text-xs font-mono max-w-xs truncate">{JSON.stringify(log.details)}</TableCell>
                                                </TableRow>
                                            ))
                                        )}
                                    </TableBody>
                                </Table>
                            </div>
                            <div className="flex items-center justify-between pt-4">
                                <p className="text-sm text-slate-500">
                                    Showing {logsData?.logs.length || 0} of {logsData?.total || 0} entries
                                </p>
                                <div className="flex gap-2">
                                    <Button variant="outline" size="sm" disabled={page <= 1 || logsLoading} onClick={() => setPage((p) => p - 1)}>Previous</Button>
                                    <Button variant="outline" size="sm" disabled={page >= (logsData?.pages || 1) || logsLoading} onClick={() => setPage((p) => p + 1)}>Next</Button>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
