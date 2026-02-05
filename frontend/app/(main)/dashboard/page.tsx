'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import Link from 'next/link';
import { Building2, ArrowRight, Activity, Calendar } from 'lucide-react';
import CompanyLogo from '@/components/CompanyLogo';

interface Company {
    id: string;
    slug: string;
    display_name: string;
    last_event_headline?: string;
    last_event_time?: string;
}

export default function DashboardPage() {
    const [companies, setCompanies] = useState<Company[]>([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const fetchUserAndData = async () => {
            try {
                const userRes = await api.get('/auth/me');
                setUser(userRes.data);
                const orgId = userRes.data.organization_id;

                if (orgId) {
                    const companiesRes = await api.get(`/org/${orgId}/companies`);
                    setCompanies(companiesRes.data);
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchUserAndData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Dashboard</h1>
                    <p className="text-slate-500 mt-1">Overview of your tracked companies and recent insights.</p>
                </div>
                <Link
                    href="/companies"
                    className="bg-slate-900 text-white px-5 py-2.5 rounded-xl font-medium shadow-lg shadow-slate-900/20 hover:bg-indigo-600 hover:shadow-indigo-600/30 transition-all flex items-center gap-2"
                >
                    <Building2 size={18} />
                    <span>Manage Companies</span>
                </Link>
            </div>

            {companies.length === 0 ? (
                <div className="glass-card rounded-3xl p-12 text-center border-dashed border-2 border-slate-300 bg-white/40">
                    <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-4 text-indigo-600">
                        <Building2 size={32} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 mb-2">No companies tracked yet</h3>
                    <p className="text-slate-500 mb-6 max-w-md mx-auto">Start tracking companies to get real-time intelligence and insights.</p>
                    <Link href="/companies" className="inline-flex items-center gap-2 text-indigo-600 font-semibold hover:text-indigo-700 hover:underline">
                        <span>Browse Companies</span>
                        <ArrowRight size={18} />
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {companies.map((company) => (
                        <Link href={`/companies/${company.id}`} key={company.id} className="block group">
                            <div className="glass-card rounded-2xl p-6 h-full flex flex-col relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full blur-3xl -mr-16 -mt-16 transition-opacity opacity-0 group-hover:opacity-100"></div>

                                <div className="flex items-start justify-between mb-4 relative z-10">
                                    <div className="flex items-center gap-3">
                                        <CompanyLogo
                                            slug={company.slug}
                                            name={company.display_name}
                                            size={48}
                                            className="shadow-sm border border-slate-100"
                                        />
                                        <h2 className="text-xl font-bold text-slate-900 group-hover:text-indigo-600 transition-colors capitalize line-clamp-1">
                                            {company.display_name}
                                        </h2>
                                    </div>
                                    <div className="p-2 bg-slate-50 rounded-lg text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                                        <ArrowRight size={18} />
                                    </div>
                                </div>

                                <p className="text-xs text-slate-400 font-medium mb-6 relative z-10 pl-1">Technology Sector</p>

                                <div className="mt-auto pt-4 border-t border-slate-100 relative z-10">
                                    {company.last_event_headline ? (
                                        <div>
                                            <div className="flex items-center gap-2 text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-2">
                                                <Activity size={14} />
                                                <span>Latest Insight</span>
                                            </div>
                                            <p className="text-slate-700 font-medium text-sm line-clamp-2 mb-3 leading-relaxed">
                                                {company.last_event_headline}
                                            </p>
                                            <div className="flex items-center gap-1.5 text-xs text-slate-400">
                                                <Calendar size={12} />
                                                <span>{new Date(company.last_event_time!).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-2 text-slate-400 italic text-sm py-2">
                                            <Activity size={16} />
                                            <span>No recent events</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
