'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Cookies from 'js-cookie';
import { jwtDecode } from 'jwt-decode';
import { ArrowLeft, Calendar, Link as LinkIcon, MessageSquare, Send, CheckCircle2, Clock, Circle, AlertCircle } from 'lucide-react';

interface Comment {
    id: string;
    user_id: string;
    text: string;
    created_at: string;
}

interface Task {
    id: string;
    title: string;
    description?: string;
    status: string;
    priority: string;
    due_date?: string;
    event_id?: string;
    assigned_to?: string;
    created_at: string;
    comments?: Comment[];
}

export default function TaskDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const [task, setTask] = useState<Task | null>(null);
    const [loading, setLoading] = useState(true);
    const [newComment, setNewComment] = useState('');
    const [orgId, setOrgId] = useState<string | null>(null);

    useEffect(() => {
        const token = Cookies.get('token');
        if (token) {
            const decoded: any = jwtDecode(token);
            setOrgId(decoded.org_id);
        }
    }, []);

    useEffect(() => {
        fetchTask();
    }, [id]);

    const fetchTask = async () => {
        try {
            const res = await api.get(`/tasks/${id}`);
            setTask(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const updateTask = async (updates: Partial<Task>) => {
        try {
            await api.patch(`/tasks/${id}`, updates);
            await fetchTask();
        } catch (err) {
            console.error(err);
        }
    };

    const addComment = async () => {
        if (!newComment.trim()) return;
        try {
            await api.post(`/tasks/${id}/comments`, { text: newComment });
            setNewComment('');
            await fetchTask();
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
    );

    if (!task) return <div className="p-8 text-center text-slate-500">Task not found</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <Link href="/tasks" className="text-slate-500 hover:text-indigo-600 text-sm mb-3 inline-flex items-center gap-1 transition-colors">
                    <ArrowLeft size={14} />
                    Back to Tasks
                </Link>
            </div>

            <div className="glass-card rounded-3xl overflow-hidden p-8 md:p-10">
                {/* Header */}
                <div className="mb-8">
                    <input
                        type="text"
                        value={task.title}
                        onChange={(e) => updateTask({ title: e.target.value })}
                        className="text-3xl font-bold text-slate-900 w-full bg-transparent border-none focus:outline-none focus:ring-0 p-0 placeholder:text-slate-300"
                        placeholder="Task Title"
                    />
                </div>

                {/* Status and Priority Controls */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 p-6 bg-slate-50/50 rounded-2xl border border-slate-100">
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Status</label>
                        <div className="relative">
                            <select
                                value={task.status}
                                onChange={(e) => updateTask({ status: e.target.value })}
                                className="w-full appearance-none bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 shadow-sm"
                            >
                                <option value="todo">To Do</option>
                                <option value="in_progress">In Progress</option>
                                <option value="done">Done</option>
                            </select>
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                                {task.status === 'done' ? <CheckCircle2 size={16} className="text-emerald-500" /> :
                                    task.status === 'in_progress' ? <Clock size={16} className="text-blue-500" /> :
                                        <Circle size={16} className="text-slate-400" />}
                            </div>
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Priority</label>
                        <div className="relative">
                            <select
                                value={task.priority}
                                onChange={(e) => updateTask({ priority: e.target.value })}
                                className="w-full appearance-none bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 shadow-sm"
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-500">
                                <AlertCircle size={16} className={
                                    task.priority === 'high' ? 'text-red-500' :
                                        task.priority === 'medium' ? 'text-amber-500' :
                                            'text-emerald-500'
                                } />
                            </div>
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Due Date</label>
                        <div className="relative">
                            <input
                                type="date"
                                value={task.due_date ? new Date(task.due_date).toISOString().split('T')[0] : ''}
                                onChange={(e) => {
                                    const newDate = e.target.value ? `${e.target.value}T00:00:00` : undefined;
                                    updateTask({ due_date: newDate });
                                }}
                                className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 shadow-sm"
                            />
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                                <Calendar size={16} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Linked Event */}
                {task.event_id && (
                    <div className="mb-8">
                        <Link
                            href={`/events/${task.event_id}`}
                            className="block p-4 bg-indigo-50/50 border border-indigo-100 rounded-xl hover:bg-indigo-50 hover:border-indigo-200 transition-all group"
                        >
                            <div className="text-xs font-bold text-indigo-600 uppercase tracking-wide mb-1 flex items-center gap-1.5">
                                <LinkIcon size={12} />
                                Linked Intelligence Event
                            </div>
                            <div className="text-indigo-900 font-medium group-hover:underline">
                                View Related Event Details →
                            </div>
                        </Link>
                    </div>
                )}

                {/* Description */}
                <div className="mb-8">
                    <label className="block text-sm font-bold text-slate-900 mb-2">Description</label>
                    <textarea
                        value={task.description || ''}
                        onChange={(e) => updateTask({ description: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 min-h-[120px] resize-y transition-all"
                        placeholder="Add a detailed description..."
                    />
                </div>

                {/* Comments Section */}
                <div className="border-t border-slate-100 pt-8">
                    <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                        <MessageSquare size={20} className="text-indigo-600" />
                        Comments
                    </h3>

                    <div className="space-y-4 mb-6">
                        {task.comments?.map((comment) => (
                            <div key={comment.id} className="bg-white border border-slate-100 rounded-2xl p-4 shadow-sm">
                                <div className="text-xs text-slate-400 mb-2 font-medium">
                                    {new Date(comment.created_at).toLocaleString()}
                                </div>
                                <div className="text-slate-700 text-sm leading-relaxed">{comment.text}</div>
                            </div>
                        ))}
                        {(!task.comments || task.comments.length === 0) && (
                            <div className="text-slate-400 text-sm italic text-center py-4">No comments yet. Start the discussion!</div>
                        )}
                    </div>

                    <div className="flex gap-3 relative">
                        <input
                            type="text"
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && addComment()}
                            placeholder="Type a comment..."
                            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                        />
                        <button
                            onClick={addComment}
                            disabled={!newComment.trim()}
                            className="absolute right-2 top-1.5 bg-indigo-600 text-white p-1.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            <Send size={16} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
