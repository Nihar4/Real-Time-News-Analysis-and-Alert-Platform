'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Users, Mail, UserPlus, Shield, Trash2, User } from 'lucide-react';

interface Member {
    id: string;
    email: string;
    name: string;
    role: string;
}

export default function AdminMembersPage() {
    const [members, setMembers] = useState<Member[]>([]);
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteName, setInviteName] = useState('');
    const [user, setUser] = useState<any>(null);
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        api.get('/auth/me').then(res => {
            setUser(res.data);
            if (res.data.role === 'admin') {
                fetchMembers(res.data.organization_id);
            }
        });
    }, []);

    const fetchMembers = async (orgId: string) => {
        try {
            const res = await api.get(`/org/${orgId}/members`);
            setMembers(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    const handleInvite = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;
        setLoading(true);
        try {
            await api.post(`/org/${user.organization_id}/invite`, {
                email: inviteEmail,
                name: inviteName
            });
            setMessage('Member invited successfully!');
            setInviteEmail('');
            setInviteName('');
            fetchMembers(user.organization_id);
            setTimeout(() => setMessage(''), 3000);
        } catch (err: any) {
            setMessage(err.response?.data?.detail || 'Failed to invite');
        } finally {
            setLoading(false);
        }
    };

    if (!user || user.role !== 'admin') {
        return (
            <div className="min-h-[60vh] flex items-center justify-center">
                <div className="text-center p-8 bg-red-50 rounded-3xl border border-red-100">
                    <Shield size={48} className="text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-bold text-red-700 mb-2">Access Denied</h2>
                    <p className="text-red-600">You must be an administrator to view this page.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Team Management</h1>
                <p className="text-slate-500 mt-1">Manage your organization members and invitations.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Invite Form */}
                <div className="lg:col-span-1">
                    <div className="glass-card rounded-3xl p-6 md:p-8 sticky top-8">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
                                <UserPlus size={20} />
                            </div>
                            <h2 className="text-xl font-bold text-slate-900">Invite Member</h2>
                        </div>

                        {message && (
                            <div className={`p-4 rounded-xl text-sm font-medium mb-6 ${message.includes('success')
                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                                    : 'bg-red-50 text-red-700 border border-red-100'
                                }`}>
                                {message}
                            </div>
                        )}

                        <form onSubmit={handleInvite} className="space-y-5">
                            <div className="space-y-2">
                                <label className="block text-sm font-bold text-slate-700 ml-1">Full Name</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                    <input
                                        type="text"
                                        value={inviteName}
                                        onChange={(e) => setInviteName(e.target.value)}
                                        className="w-full bg-white/50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                                        placeholder="Jane Smith"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-bold text-slate-700 ml-1">Email Address</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                    <input
                                        type="email"
                                        value={inviteEmail}
                                        onChange={(e) => setInviteEmail(e.target.value)}
                                        className="w-full bg-white/50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                                        placeholder="jane@company.com"
                                        required
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-slate-900 text-white py-3.5 rounded-xl font-bold shadow-lg shadow-slate-900/20 hover:bg-indigo-600 hover:shadow-indigo-600/30 transition-all active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loading ? 'Sending Invite...' : 'Send Invitation'}
                            </button>
                        </form>
                    </div>
                </div>

                {/* Members List */}
                <div className="lg:col-span-2">
                    <div className="glass-card rounded-3xl overflow-hidden">
                        <div className="p-6 border-b border-slate-100 bg-slate-50/30 flex justify-between items-center">
                            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                                <Users size={20} className="text-indigo-600" />
                                Team Members
                            </h2>
                            <span className="bg-slate-200 text-slate-600 text-xs font-bold px-2.5 py-1 rounded-full">
                                {members.length} Active
                            </span>
                        </div>

                        <div className="divide-y divide-slate-100">
                            {members.map((member) => (
                                <div key={member.id} className="p-6 flex items-center justify-between hover:bg-slate-50/50 transition-colors group">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-100 to-violet-100 border border-indigo-200 flex items-center justify-center text-indigo-700 font-bold shadow-sm">
                                            {member.name.charAt(0)}
                                        </div>
                                        <div>
                                            <p className="font-bold text-slate-900">{member.name}</p>
                                            <p className="text-sm text-slate-500">{member.email}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${member.role === 'admin'
                                                ? 'bg-purple-50 text-purple-700 border-purple-100'
                                                : 'bg-slate-100 text-slate-600 border-slate-200'
                                            }`}>
                                            {member.role}
                                        </span>
                                        {/* Placeholder for future actions like Remove Member */}
                                        {/* <button className="text-slate-300 hover:text-red-500 transition-colors p-2">
                                            <Trash2 size={18} />
                                        </button> */}
                                    </div>
                                </div>
                            ))}
                            {members.length === 0 && (
                                <div className="p-12 text-center text-slate-500">
                                    No members found. Invite someone to get started!
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
