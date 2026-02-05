'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import Link from 'next/link';
import Cookies from 'js-cookie';
import { jwtDecode } from 'jwt-decode';
import CreateTaskModal from '@/components/tasks/CreateTaskModal';
import { Plus, ArrowLeft, Calendar, Link as LinkIcon, CheckCircle2, Circle, Clock } from 'lucide-react';

interface Task {
    id: string;
    title: string;
    status: string;
    priority: string;
    due_date?: string;
    event_id?: string;
    assigned_to?: string;
    created_at: string;
}

export default function TaskListPage() {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('');
    const [orgId, setOrgId] = useState<string | null>(null);
    const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);

    useEffect(() => {
        const token = Cookies.get('token');
        if (token) {
            const decoded: any = jwtDecode(token);
            setOrgId(decoded.org_id);
        }
    }, []);

    useEffect(() => {
        if (orgId) {
            fetchTasks();
        }
    }, [orgId, statusFilter]);

    const fetchTasks = async () => {
        if (!orgId) return;
        try {
            const params = statusFilter ? `?status=${statusFilter}` : '';
            const res = await api.get(`/tasks/org/${orgId}/tasks${params}`);
            setTasks(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusConfig = (status: string) => {
        switch (status) {
            case 'todo': return { color: 'bg-slate-100 text-slate-600', icon: Circle, label: 'To Do' };
            case 'in_progress': return { color: 'bg-blue-50 text-blue-600', icon: Clock, label: 'In Progress' };
            case 'done': return { color: 'bg-emerald-50 text-emerald-600', icon: CheckCircle2, label: 'Done' };
            default: return { color: 'bg-slate-100 text-slate-600', icon: Circle, label: status };
        }
    };

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'low': return 'bg-emerald-50 text-emerald-700 border-emerald-100';
            case 'medium': return 'bg-amber-50 text-amber-700 border-amber-100';
            case 'high': return 'bg-red-50 text-red-700 border-red-100';
            default: return 'bg-slate-50 text-slate-700 border-slate-100';
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <Link href="/dashboard" className="text-slate-500 hover:text-indigo-600 text-sm mb-2 inline-flex items-center gap-1 transition-colors">
                        <ArrowLeft size={14} />
                        Back to Dashboard
                    </Link>
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Tasks</h1>
                </div>
                <button
                    onClick={() => setIsTaskModalOpen(true)}
                    className="flex items-center gap-2 bg-slate-900 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-600 shadow-lg shadow-slate-900/20 hover:shadow-indigo-600/30 transition-all active:scale-95"
                >
                    <Plus size={18} />
                    Create Task
                </button>
            </div>

            {/* Filters */}
            <div className="flex gap-4">
                <div className="relative">
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="appearance-none bg-white border border-slate-200 rounded-xl px-4 py-2.5 pr-10 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 shadow-sm"
                    >
                        <option value="">All Status</option>
                        <option value="todo">To Do</option>
                        <option value="in_progress">In Progress</option>
                        <option value="done">Done</option>
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Task List */}
            <div className="glass-card rounded-3xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-100">
                        <thead className="bg-slate-50/50">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Title</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Priority</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Due Date</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Linked Event</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 bg-white/40">
                            {tasks.map((task) => {
                                const statusConfig = getStatusConfig(task.status);
                                const StatusIcon = statusConfig.icon;

                                return (
                                    <tr
                                        key={task.id}
                                        className="hover:bg-slate-50/80 cursor-pointer transition-colors group"
                                        onClick={() => window.location.href = `/tasks/${task.id}`}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">{task.title}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-3 py-1 inline-flex items-center gap-1.5 text-xs font-medium rounded-full ${statusConfig.color}`}>
                                                <StatusIcon size={12} />
                                                {statusConfig.label}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-3 py-1 inline-flex text-xs font-medium rounded-full border ${getPriorityColor(task.priority)} capitalize`}>
                                                {task.priority}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                                            {task.due_date ? (
                                                <div className="flex items-center gap-1.5">
                                                    <Calendar size={14} className="text-slate-400" />
                                                    {new Date(task.due_date).toLocaleDateString()}
                                                </div>
                                            ) : '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            {task.event_id ? (
                                                <Link
                                                    href={`/events/${task.event_id}`}
                                                    className="inline-flex items-center gap-1.5 text-indigo-600 hover:text-indigo-700 font-medium hover:underline"
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    <LinkIcon size={14} />
                                                    View Event
                                                </Link>
                                            ) : <span className="text-slate-400">-</span>}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
                {tasks.length === 0 && (
                    <div className="p-12 text-center">
                        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
                            <CheckCircle2 size={32} />
                        </div>
                        <p className="text-slate-500 font-medium">No tasks found.</p>
                        <p className="text-slate-400 text-sm mt-1">Create a task to get started!</p>
                    </div>
                )}
            </div>

            <CreateTaskModal
                isOpen={isTaskModalOpen}
                onClose={() => setIsTaskModalOpen(false)}
                onTaskCreated={fetchTasks}
            />
        </div>
    );
}
