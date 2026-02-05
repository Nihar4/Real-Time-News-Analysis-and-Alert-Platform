'use client';

import { usePathname, useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { LogOut, Bell, Search, ChevronDown } from 'lucide-react';

export default function Navbar() {
    const pathname = usePathname();
    const router = useRouter();
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const token = Cookies.get('token');
        if (token) {
            api.get('/auth/me')
                .then(res => setUser(res.data))
                .catch(() => {
                    Cookies.remove('token');
                    setUser(null);
                });
        }
    }, [pathname]);

    const logout = () => {
        Cookies.remove('token');
        setUser(null);
        router.push('/login');
    };

    if (pathname === '/login' || pathname === '/signup') return null;
    if (!user) return null;

    return (
        <header className="h-full glass-panel rounded-2xl flex items-center justify-between px-6">
            {/* Left: Search / Breadcrumbs (Placeholder) */}
            <div className="flex items-center gap-4 flex-1">
                <div className="relative group w-full max-w-md hidden md:block">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={18} />
                    <input
                        type="text"
                        placeholder="Search intelligence..."
                        className="w-full bg-slate-50/50 border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400"
                    />
                </div>
            </div>

            {/* Right: Actions & Profile */}
            <div className="flex items-center gap-6">
                {/* Notifications */}
                <button className="relative p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all">
                    <Bell size={20} />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
                </button>

                <div className="h-8 w-px bg-slate-200"></div>

                {/* Profile Dropdown Trigger */}
                <div className="flex items-center gap-3 group cursor-pointer">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-semibold text-slate-700 group-hover:text-indigo-700 transition-colors">
                            {user.name || user.email}
                        </p>
                        <p className="text-xs text-slate-500 font-medium">
                            {user.organization_name} • <span className="capitalize">{user.role}</span>
                        </p>
                    </div>

                    <div className="relative">
                        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 border border-indigo-200 flex items-center justify-center text-indigo-700 font-bold shadow-sm group-hover:shadow-md transition-all">
                            {(user.name || user.email)[0].toUpperCase()}
                        </div>
                        <div className="absolute -bottom-1 -right-1 bg-white rounded-full p-0.5 border border-slate-100 shadow-sm">
                            <ChevronDown size={12} className="text-slate-400" />
                        </div>
                    </div>

                    <button
                        onClick={logout}
                        className="ml-2 p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                        title="Logout"
                    >
                        <LogOut size={18} />
                    </button>
                </div>
            </div>
        </header>
    );
}
