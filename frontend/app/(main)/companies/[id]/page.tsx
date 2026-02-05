'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Trash2, Calendar, Activity, Building2 } from 'lucide-react';
import CompanyLogo from '@/components/CompanyLogo';

interface Event {
    id: string;
    headline_summary: string;
    short_summary: string;
    event_type: string;
    created_at: string;
}

export default function CompanyDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const [events, setEvents] = useState<Event[]>([]);
    const [companyName, setCompanyName] = useState('');
    const [companySlug, setCompanySlug] = useState('');
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<any>(null);
    const router = useRouter();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const userRes = await api.get('/auth/me');
                setUser(userRes.data);
                const orgId = userRes.data.organization_id;

                if (orgId) {
                    // Fetch events
                    const eventsRes = await api.get(`/org/${orgId}/companies/${id}/events`);
                    setEvents(eventsRes.data);

                    // Fetch company details (from list for now)
                    const companiesRes = await api.get(`/org/${orgId}/companies`);
                    const company = companiesRes.data.find((c: any) => c.id === id);
                    if (company) {
                        setCompanyName(company.display_name);
                        setCompanySlug(company.slug);
                    }
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    const handleUnsubscribe = async () => {
        if (!confirm('Are you sure you want to unsubscribe from this company?')) return;
        try {
            await api.delete(`/org/${user.organization_id}/companies/${id}`);
            router.push('/dashboard');
        } catch (err) {
            alert('Failed to unsubscribe');
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
    );

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div>
                    <Link href="/dashboard" className="text-slate-500 hover:text-indigo-600 text-sm mb-3 inline-flex items-center gap-1 transition-colors">
                        <ArrowLeft size={14} />
                        Back to Dashboard
                    </Link>
                    <div className="flex items-center gap-4">
                        {companySlug ? (
                            <CompanyLogo
                                slug={companySlug}
                                name={companyName}
                                size={64}
                                className="shadow-md border border-slate-200"
                            />
                        ) : (
                            <div className="w-16 h-16 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-indigo-600 font-bold shadow-sm">
                                <Building2 size={32} />
                            </div>
                        )}
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900 tracking-tight capitalize">{companyName || 'Company Intelligence'}</h1>
                            <p className="text-slate-500 text-sm font-medium">{events.length} Intelligence Events Tracked</p>
                        </div>
                    </div>
                </div>
                {user?.role === 'admin' && (
                    <button
                        onClick={handleUnsubscribe}
                        className="bg-white border border-red-200 text-red-600 px-4 py-2.5 rounded-xl hover:bg-red-50 text-sm font-medium flex items-center gap-2 transition-colors shadow-sm"
                    >
                        <Trash2 size={16} />
                        Unsubscribe Company
                    </button>
                )}
            </div>

            <div className="space-y-4">
                {events.length > 0 && (
                    <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 px-1">
                        <Activity size={20} className="text-indigo-600" />
                        Recent Activity
                    </h2>
                )}

                {events.map((event) => (
                    <Link href={`/events/${event.id}`} key={event.id} className="block group">
                        <div className="glass-card rounded-2xl p-6 md:p-8 hover:bg-white/80 transition-all">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex gap-2">
                                    <span className="bg-indigo-50 text-indigo-700 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide border border-indigo-100">
                                        {event.event_type || 'News'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1.5 text-slate-400 text-sm font-medium">
                                    <Calendar size={14} />
                                    <span>
                                        {new Date(event.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                    </span>
                                </div>
                            </div>
                            <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-indigo-600 transition-colors leading-tight">
                                {event.headline_summary}
                            </h3>
                            <p className="text-slate-600 line-clamp-2 text-base leading-relaxed">
                                {event.short_summary}
                            </p>
                        </div>
                    </Link>
                ))}

                {events.length === 0 && (
                    <div className="glass-card rounded-3xl p-16 text-center border-dashed border-2 border-slate-300 bg-slate-50/50">
                        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
                            <Activity size={32} />
                        </div>
                        <h3 className="text-lg font-bold text-slate-900 mb-1">No events found</h3>
                        <p className="text-slate-500">We haven't detected any intelligence events for this company yet.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
