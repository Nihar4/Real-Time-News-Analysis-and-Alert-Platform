'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Search, Building2, Check, Plus, Trash2, ArrowRight } from 'lucide-react';
import CompanyLogo from '@/components/CompanyLogo';

interface Company {
    id: string;
    slug: string;
    display_name: string;
}

export default function CompaniesPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<Company[]>([]);
    const [subscribedCompanies, setSubscribedCompanies] = useState<Company[]>([]);
    const [subscribedIds, setSubscribedIds] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<any>(null);
    const [searchLoading, setSearchLoading] = useState(false);
    const router = useRouter();

    useEffect(() => {
        fetchSubscribedCompanies();
    }, []);

    // Debounced search effect
    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchQuery.trim().length >= 2) {
                handleSearch();
            } else {
                setSearchResults([]);
            }
        }, 300); // 300ms delay

        return () => clearTimeout(timer);
    }, [searchQuery]);

    const fetchSubscribedCompanies = async () => {
        try {
            const userRes = await api.get('/auth/me');
            setUser(userRes.data);
            const orgId = userRes.data.organization_id;

            if (orgId) {
                const res = await api.get(`/org/${orgId}/companies`);
                setSubscribedCompanies(res.data);
                setSubscribedIds(new Set(res.data.map((c: any) => c.id)));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setSearchLoading(true);
        try {
            const res = await api.get(`/companies?query=${searchQuery}`);
            setSearchResults(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setSearchLoading(false);
        }
    };

    const handleSubscribe = async (companyId: string) => {
        try {
            await api.post(`/org/${user.organization_id}/companies/subscribe`, { company_id: companyId });
            // Refresh list to see new sub
            fetchSubscribedCompanies();
            // Update local state to show checkmark immediately
            setSubscribedIds(prev => new Set(prev).add(companyId));
        } catch (err) {
            alert('Failed to subscribe');
        }
    };

    const handleUnsubscribe = async (companyId: string) => {
        if (!confirm('Unsubscribe from this company?')) return;
        try {
            await api.delete(`/org/${user.organization_id}/companies/${companyId}`);
            fetchSubscribedCompanies();
            const newSet = new Set(subscribedIds);
            newSet.delete(companyId);
            setSubscribedIds(newSet);
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
        <div className="max-w-6xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Company Intelligence</h1>
                <p className="text-slate-500 mt-1">Manage your tracked companies and discover new ones.</p>
            </div>

            {/* Admin Section: Search & Subscribe */}
            {user?.role === 'admin' && (
                <div className="glass-card rounded-3xl p-6 md:p-8">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                            <Search size={20} className="text-indigo-600" />
                            Find & Track Companies
                        </h2>
                        <span className="bg-indigo-100 text-indigo-700 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">Admin Mode</span>
                    </div>

                    <div className="relative">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Type to search companies (e.g. 'Google', 'Tesla')..."
                            className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-12 pr-4 py-3.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400"
                        />
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                            <Search size={20} />
                        </div>
                        {searchLoading && (
                            <div className="absolute right-4 top-1/2 -translate-y-1/2">
                                <div className="animate-spin h-5 w-5 border-2 border-indigo-500 rounded-full border-t-transparent"></div>
                            </div>
                        )}
                    </div>

                    {/* Search Results Dropdown/List */}
                    {searchResults.length > 0 && (
                        <div className="mt-4 border border-slate-200 rounded-xl overflow-hidden shadow-sm bg-white">
                            <table className="min-w-full divide-y divide-slate-100">
                                <thead className="bg-slate-50/50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</th>
                                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {searchResults.map((company) => (
                                        <tr key={company.id} className="hover:bg-slate-50/80 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-3">
                                                    <CompanyLogo
                                                        slug={company.slug}
                                                        name={company.display_name}
                                                        size={32}
                                                        className="border border-slate-100"
                                                    />
                                                    <div>
                                                        <div className="text-sm font-semibold text-slate-900 capitalize">{company.display_name}</div>
                                                        <div className="text-xs text-slate-500">Slug: {company.slug}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                {subscribedIds.has(company.id) ? (
                                                    <span className="text-emerald-600 font-bold flex items-center justify-end gap-1.5 bg-emerald-50 px-3 py-1 rounded-full inline-flex">
                                                        <Check size={14} />
                                                        Subscribed
                                                    </span>
                                                ) : (
                                                    <button
                                                        onClick={() => handleSubscribe(company.id)}
                                                        className="text-white bg-indigo-600 hover:bg-indigo-700 px-4 py-1.5 rounded-lg text-sm font-medium transition-all shadow-sm hover:shadow-indigo-200"
                                                    >
                                                        Subscribe
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {searchQuery.length >= 2 && searchResults.length === 0 && !searchLoading && (
                        <p className="text-slate-500 mt-4 text-sm italic text-center py-2">No companies found matching "{searchQuery}".</p>
                    )}
                </div>
            )}

            {/* SHARED VIEW: Subscribed Companies List */}
            <div className="glass-card rounded-3xl overflow-hidden">
                <div className="p-6 border-b border-slate-100 bg-slate-50/30">
                    <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                        <Building2 size={20} className="text-indigo-600" />
                        Subscribed Companies
                    </h2>
                </div>

                <div className="divide-y divide-slate-100">
                    {subscribedCompanies.length === 0 ? (
                        <div className="p-12 text-center">
                            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
                                <Building2 size={32} />
                            </div>
                            <p className="text-slate-500 font-medium">No companies subscribed yet.</p>
                            <p className="text-slate-400 text-sm mt-1">Search above to add companies to your watchlist.</p>
                        </div>
                    ) : (
                        subscribedCompanies.map((company) => (
                            <div key={company.id} className="p-6 flex justify-between items-center hover:bg-slate-50/50 transition-colors group">
                                <div onClick={() => router.push(`/companies/${company.id}`)} className="cursor-pointer flex-1 flex items-center gap-4">
                                    <CompanyLogo
                                        slug={company.slug}
                                        name={company.display_name}
                                        size={48}
                                        className="shadow-sm border border-slate-100 bg-white"
                                    />
                                    <div>
                                        <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors capitalize">{company.display_name}</h3>
                                        <p className="text-slate-500 text-sm">@{company.slug}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={() => router.push(`/companies/${company.id}`)}
                                        className="text-slate-400 hover:text-indigo-600 p-2 rounded-lg hover:bg-indigo-50 transition-colors"
                                    >
                                        <ArrowRight size={20} />
                                    </button>
                                    {user?.role === 'admin' && (
                                        <button
                                            onClick={() => handleUnsubscribe(company.id)}
                                            className="text-slate-400 hover:text-red-600 p-2 rounded-lg hover:bg-red-50 transition-colors"
                                            title="Unsubscribe"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
