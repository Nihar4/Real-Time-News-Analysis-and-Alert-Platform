'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import Cookies from 'js-cookie';
import api from '@/lib/api';
import { LayoutDashboard, Building2, Users, CheckSquare, ShieldCheck } from 'lucide-react';

export default function Sidebar() {
    const pathname = usePathname();
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const token = Cookies.get('token');
        if (token) {
            api.get('/auth/me')
                .then(res => setUser(res.data))
                .catch(() => setUser(null));
        }
    }, [pathname]);

    if (pathname === '/login' || pathname === '/signup') return null;
    if (!user) return null;

    const isActive = (path: string) => pathname.startsWith(path);

    const NavItem = ({ href, icon: Icon, label, active }: { href: string; icon: any; label: string; active: boolean }) => (
        <Link
            href={href}
            className={`
                group flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-200 font-medium
                ${active
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30 translate-x-1'
                    : 'text-slate-500 hover:bg-white/50 hover:text-indigo-600 hover:shadow-sm hover:translate-x-1'
                }
            `}
        >
            <Icon size={20} className={`transition-transform duration-200 ${active ? '' : 'group-hover:scale-110'}`} />
            <span>{label}</span>
        </Link>
    );

    return (
        <aside className="h-full flex flex-col glass-panel rounded-3xl overflow-hidden">
            <div className="p-8 pb-6">
                <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">
                        <ShieldCheck size={24} />
                    </div>
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600 tracking-tight">
                        FutureFeed
                    </h1>
                </div>
                <p className="text-xs text-slate-400 font-medium pl-1">Competitor Intelligence</p>
            </div>

            <nav className="flex-1 px-4 space-y-2 overflow-y-auto py-4">
                <div className="px-4 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Menu
                </div>

                <NavItem
                    href="/dashboard"
                    icon={LayoutDashboard}
                    label="Dashboard"
                    active={isActive('/dashboard')}
                />

                <NavItem
                    href="/companies"
                    icon={Building2}
                    label="Companies"
                    active={isActive('/companies')}
                />

                <NavItem
                    href="/tasks"
                    icon={CheckSquare}
                    label="Tasks"
                    active={isActive('/tasks')}
                />

                {user.role === 'admin' && (
                    <>
                        <div className="px-4 py-2 mt-6 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                            Administration
                        </div>
                        <NavItem
                            href="/admin/members"
                            icon={Users}
                            label="Members"
                            active={isActive('/admin/members')}
                        />
                    </>
                )}
            </nav>
        </aside>
    );
}
