'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import Cookies from 'js-cookie';
import { Eye, EyeOff, CheckCircle, XCircle, ShieldCheck, ArrowRight } from 'lucide-react';

export default function InvitePage() {
    const params = useParams();
    const router = useRouter();
    const token = params.token as string;

    const [loading, setLoading] = useState(true);
    const [validating, setValidating] = useState(false);
    const [tokenValid, setTokenValid] = useState(false);
    const [userEmail, setUserEmail] = useState('');
    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        validateToken();
    }, [token]);

    const validateToken = async () => {
        if (!token) {
            setError('Invalid invitation link.');
            setLoading(false);
            return;
        }

        setLoading(true);
        try {
            const res = await api.post('/auth/validate-token', null, {
                params: { token }
            });

            if (res.data.valid) {
                setTokenValid(true);
                setUserEmail(res.data.email);
                setUserName(res.data.name);
            } else {
                setTokenValid(false);
                setError('This invitation link is invalid or has expired.');
            }
        } catch (err: any) {
            console.error('Validation error:', err);
            setTokenValid(false);
            setError(err.response?.data?.detail || 'Failed to validate invitation. Please contact your administrator.');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validation
        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setValidating(true);
        try {
            const res = await api.post('/auth/setup-password', {
                token,
                password
            });

            // Save token and redirect to dashboard
            Cookies.set('token', res.data.access_token, { expires: 7 });
            setSuccess(true);

            // Redirect after 2 seconds
            setTimeout(() => {
                router.push('/dashboard');
            }, 2000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to set password. Please try again.');
        } finally {
            setValidating(false);
        }
    };

    // Shared background component
    const Background = () => (
        <div className="fixed inset-0 -z-10 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-slate-50 to-cyan-50"></div>
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-200/20 rounded-full blur-3xl opacity-60 mix-blend-multiply filter"></div>
            <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-indigo-200/20 rounded-full blur-3xl opacity-60 mix-blend-multiply filter"></div>
        </div>
    );

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center relative font-sans text-slate-800">
                <Background />
                <div className="text-center p-8 bg-white/40 backdrop-blur-xl rounded-2xl border border-white/50 shadow-xl">
                    <div className="relative">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="h-6 w-6 bg-white rounded-full opacity-50"></div>
                        </div>
                    </div>
                    <p className="mt-6 text-slate-600 font-medium animate-pulse">Verifying secure invitation...</p>
                </div>
            </div>
        );
    }

    if (!tokenValid) {
        return (
            <div className="min-h-screen flex items-center justify-center relative px-4 font-sans text-slate-800">
                <Background />
                <div className="bg-white/70 backdrop-blur-xl p-10 rounded-3xl shadow-2xl shadow-slate-200/50 max-w-md w-full text-center border border-white/60 animate-in fade-in zoom-in duration-300">
                    <div className="mx-auto bg-red-50 w-20 h-20 rounded-full flex items-center justify-center mb-6 shadow-inner">
                        <XCircle className="text-red-500" size={40} />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 mb-3 tracking-tight">Invitation Invalid</h1>
                    <p className="text-slate-500 mb-8 leading-relaxed">{error}</p>
                    <a
                        href="/login"
                        className="inline-flex items-center justify-center w-full px-6 py-3 text-sm font-semibold text-white transition-all bg-slate-900 rounded-xl hover:bg-slate-800 hover:shadow-lg hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
                    >
                        Return to Login
                    </a>
                </div>
            </div>
        );
    }

    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center relative px-4 font-sans text-slate-800">
                <Background />
                <div className="bg-white/70 backdrop-blur-xl p-10 rounded-3xl shadow-2xl shadow-indigo-200/50 max-w-md w-full text-center border border-white/60 animate-in fade-in zoom-in duration-300">
                    <div className="mx-auto bg-green-50 w-20 h-20 rounded-full flex items-center justify-center mb-6 shadow-inner">
                        <CheckCircle className="text-green-500" size={40} />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 mb-3 tracking-tight">All Set!</h1>
                    <p className="text-slate-500 mb-8">Your password has been secured. Redirecting you to the dashboard...</p>
                    <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div className="bg-indigo-600 h-1.5 rounded-full animate-[progress_2s_ease-in-out_infinite] w-full origin-left"></div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center relative px-4 py-12 font-sans text-slate-800">
            <Background />

            <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Brand / Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-500/30 mb-4">
                        <ShieldCheck size={24} />
                    </div>
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Welcome to NewsInsight</h1>
                    <p className="text-slate-500 text-lg">Set up your secure access</p>
                </div>

                {/* Main Card */}
                <div className="bg-white/80 backdrop-blur-xl p-8 md:p-10 rounded-3xl shadow-2xl shadow-indigo-100/50 border border-white/60">

                    {/* User Info Badge */}
                    <div className="bg-indigo-50/50 border border-indigo-100 rounded-2xl p-4 mb-8 flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-lg">
                            {userName.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-slate-900 truncate">{userName}</p>
                            <p className="text-xs text-slate-500 truncate">{userEmail}</p>
                        </div>
                        <div className="text-xs font-medium text-indigo-600 bg-indigo-100/50 px-2 py-1 rounded-md">
                            Invited
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-5">
                            <div className="group">
                                <label className="block text-sm font-semibold text-slate-700 mb-2 ml-1">
                                    Create Password
                                </label>
                                <div className="relative transition-all duration-200 focus-within:transform focus-within:scale-[1.01]">
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3.5 pr-12 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm group-hover:border-slate-300"
                                        placeholder="••••••••"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-indigo-600 transition-colors rounded-lg hover:bg-indigo-50"
                                    >
                                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                                <div className="flex items-center gap-2 mt-2 ml-1">
                                    <div className={`h-1 flex-1 rounded-full transition-all duration-300 ${password.length > 0 ? (password.length >= 8 ? 'bg-green-500' : 'bg-amber-400') : 'bg-slate-100'}`}></div>
                                    <div className={`h-1 flex-1 rounded-full transition-all duration-300 ${password.length >= 8 ? 'bg-green-500' : 'bg-slate-100'}`}></div>
                                    <div className={`h-1 flex-1 rounded-full transition-all duration-300 ${password.length >= 12 ? 'bg-green-500' : 'bg-slate-100'}`}></div>
                                </div>
                                <p className="text-xs text-slate-500 mt-1.5 ml-1">Must be at least 8 characters</p>
                            </div>

                            <div className="group">
                                <label className="block text-sm font-semibold text-slate-700 mb-2 ml-1">
                                    Confirm Password
                                </label>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3.5 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm group-hover:border-slate-300 focus:transform focus:scale-[1.01]"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="bg-red-50/80 backdrop-blur-sm border border-red-100 rounded-xl p-4 flex items-start gap-3 animate-in fade-in slide-in-from-top-2">
                                <XCircle className="text-red-600 shrink-0 mt-0.5" size={18} />
                                <p className="text-sm font-medium text-red-800">{error}</p>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={validating}
                            className="w-full group relative overflow-hidden bg-slate-900 text-white px-6 py-4 rounded-xl font-semibold shadow-lg shadow-slate-900/20 hover:bg-indigo-600 hover:shadow-indigo-600/30 active:scale-[0.98] transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed disabled:active:scale-100"
                        >
                            <span className="relative z-10 flex items-center justify-center gap-2">
                                {validating ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"></div>
                                        <span>Securing Account...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Set Password & Continue</span>
                                        <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                    </>
                                )}
                            </span>
                        </button>
                    </form>
                </div>

                {/* Footer */}
                <p className="text-center text-slate-400 text-sm mt-8">
                    &copy; {new Date().getFullYear()} NewsInsight. All rights reserved.
                </p>
            </div>
        </div>
    );
}
