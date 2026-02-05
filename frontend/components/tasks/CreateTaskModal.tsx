'use client';

import { useState, useEffect, useRef } from 'react';
import api from '@/lib/api';
import Cookies from 'js-cookie';
import { jwtDecode } from 'jwt-decode';
import { X, Search, User, Calendar, Flag, AlignLeft, CheckSquare } from 'lucide-react';

interface CreateTaskModalProps {
    isOpen: boolean;
    onClose: () => void;
    eventId?: string;
    initialTitle?: string;
    onTaskCreated?: () => void;
}

interface OrgMember {
    id: string;
    name: string;
    email: string;
    role: string;
}

export default function CreateTaskModal({ isOpen, onClose, eventId, initialTitle, onTaskCreated }: CreateTaskModalProps) {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [priority, setPriority] = useState('medium');
    const [dueDate, setDueDate] = useState('');
    const [assignedTo, setAssignedTo] = useState('');
    const [loading, setLoading] = useState(false);
    const [orgId, setOrgId] = useState<string | null>(null);

    // User search states
    const [users, setUsers] = useState<OrgMember[]>([]);
    const [filteredUsers, setFilteredUsers] = useState<OrgMember[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [showDropdown, setShowDropdown] = useState(false);
    const [selectedUser, setSelectedUser] = useState<OrgMember | null>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const token = Cookies.get('token');
        if (token) {
            const decoded: any = jwtDecode(token);
            setOrgId(decoded.org_id);
        }
    }, []);

    useEffect(() => {
        if (orgId) {
            fetchUsers();
        }
    }, [orgId]);

    useEffect(() => {
        if (initialTitle) {
            setTitle(initialTitle);
        }
    }, [initialTitle]);

    useEffect(() => {
        // Filter users based on search query
        if (searchQuery) {
            const filtered = users.filter(user =>
                user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                user.email.toLowerCase().includes(searchQuery.toLowerCase())
            );
            setFilteredUsers(filtered);
        } else {
            setFilteredUsers(users);
        }
    }, [searchQuery, users]);

    // Click outside to close dropdown
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const fetchUsers = async () => {
        if (!orgId) return;
        try {
            const res = await api.get(`/org/${orgId}/members`);
            setUsers(res.data);
            setFilteredUsers(res.data);
        } catch (err) {
            console.error('Failed to fetch users:', err);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!orgId) return;

        setLoading(true);
        try {
            // Convert date to datetime format (append midnight time)
            const dueDatetime = dueDate ? `${dueDate}T00:00:00` : null;

            await api.post(`/tasks/org/${orgId}/tasks`, {
                title,
                description,
                priority,
                due_date: dueDatetime,
                assigned_to: selectedUser?.id || null,
                event_id: eventId || null
            });
            onTaskCreated?.();
            onClose();
            // Reset form
            setTitle('');
            setDescription('');
            setPriority('medium');
            setDueDate('');
            setAssignedTo('');
            setSelectedUser(null);
            setSearchQuery('');
        } catch (err) {
            console.error('Failed to create task:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleUserSelect = (user: OrgMember) => {
        setSelectedUser(user);
        setAssignedTo(user.id);
        setSearchQuery(user.name);
        setShowDropdown(false);
    };

    const clearAssignee = () => {
        setSelectedUser(null);
        setAssignedTo('');
        setSearchQuery('');
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white w-full max-w-lg rounded-3xl overflow-hidden animate-in fade-in zoom-in duration-300 shadow-2xl shadow-indigo-500/20 flex flex-col max-h-[90vh]">
                <div className="p-6 border-b border-white/50 flex justify-between items-center bg-white/40">
                    <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                        <CheckSquare className="text-indigo-600" size={24} />
                        Create New Task
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-2 rounded-full transition-all"
                    >
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 md:p-8 space-y-6 overflow-y-auto">
                    <div className="space-y-2">
                        <label className="block text-sm font-bold text-slate-700 ml-1">Task Title</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full bg-white/50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                            placeholder="e.g., Review Q3 Competitor Report"
                            required
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="block text-sm font-bold text-slate-700 ml-1">Priority</label>
                            <div className="relative">
                                <Flag className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                                <select
                                    value={priority}
                                    onChange={(e) => setPriority(e.target.value)}
                                    className="w-full bg-white/50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 appearance-none transition-all"
                                >
                                    <option value="low">Low Priority</option>
                                    <option value="medium">Medium Priority</option>
                                    <option value="high">High Priority</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="block text-sm font-bold text-slate-700 ml-1">Due Date</label>
                            <div className="relative">
                                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                                <input
                                    type="date"
                                    value={dueDate}
                                    onChange={(e) => setDueDate(e.target.value)}
                                    className="w-full bg-white/50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="space-y-2" ref={dropdownRef}>
                        <label className="block text-sm font-bold text-slate-700 ml-1">Assignee</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => {
                                    setSearchQuery(e.target.value);
                                    setShowDropdown(true);
                                }}
                                onFocus={() => setShowDropdown(true)}
                                placeholder="Search team member..."
                                className="w-full bg-white/50 border border-slate-200 rounded-xl pl-10 pr-10 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                            />
                            {selectedUser && (
                                <button
                                    type="button"
                                    onClick={clearAssignee}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-slate-100"
                                >
                                    <X size={16} />
                                </button>
                            )}

                            {showDropdown && filteredUsers.length > 0 && (
                                <div className="absolute z-10 w-full mt-2 bg-white border border-slate-100 rounded-xl shadow-xl max-h-60 overflow-y-auto animate-in fade-in slide-in-from-top-2 duration-200">
                                    {filteredUsers.map((user) => (
                                        <button
                                            key={user.id}
                                            type="button"
                                            onClick={() => handleUserSelect(user)}
                                            className={`w-full px-4 py-3 text-left hover:bg-indigo-50 flex items-center gap-3 transition-colors ${selectedUser?.id === user.id ? 'bg-indigo-50' : ''}`}
                                        >
                                            <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs">
                                                {user.name.charAt(0)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-bold text-slate-900 truncate">{user.name}</div>
                                                <div className="text-xs text-slate-500 truncate">{user.email}</div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="block text-sm font-bold text-slate-700 ml-1">Description</label>
                        <div className="relative">
                            <AlignLeft className="absolute left-3 top-4 text-slate-400" size={18} />
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full bg-white/50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 min-h-[100px] resize-none transition-all"
                                placeholder="Add details about this task..."
                            />
                        </div>
                    </div>

                    <div className="pt-4 flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-6 py-3.5 border border-slate-200 rounded-xl text-slate-600 font-semibold hover:bg-slate-50 transition-all"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-3.5 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/40 active:scale-[0.98] transition-all disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Creating...' : 'Create Task'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
