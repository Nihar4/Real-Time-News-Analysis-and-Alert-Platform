'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { CheckSquare, Plus, ArrowLeft, Calendar, ShieldAlert, TrendingUp, BarChart3, AlertTriangle, Lightbulb, Target, Users, Globe, ShoppingBag, Zap } from 'lucide-react';
import CreateTaskModal from '@/components/tasks/CreateTaskModal';
import Cookies from 'js-cookie';
import { jwtDecode } from 'jwt-decode';

interface Event {
    id: string;
    headline_summary: string;
    short_summary: string;
    detailed_summary: string;
    event_type: string;
    created_at: string;
    primary_company_name?: string;

    // New fields
    overall_impact?: number;
    importance_level?: string;
    urgency?: string;
    time_horizon?: string;
    key_points?: string[];
    recommended_teams?: string[];
    affected_areas?: string[];
    confidence_explanation?: string;

    risk_score?: number;
    opportunity_score?: number;
    sentiment?: string;
    sentiment_score?: number;
    threat_level?: string;
    confidence_level?: string;
    recommended_actions?: string;
    tags?: string[];

    impact_on_market?: string;
    impact_on_products?: string;
    impact_on_competitors?: string;
    impact_on_customers?: string;
}

interface Task {
    id: string;
    title: string;
    status: string;
}

export default function EventDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const [event, setEvent] = useState<any>(null); // Using any to accommodate all dynamic fields
    const [loading, setLoading] = useState(true);
    const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
    const [relatedTasks, setRelatedTasks] = useState<Task[]>([]);
    const [orgId, setOrgId] = useState<string | null>(null);

    useEffect(() => {
        const token = Cookies.get('token');
        if (token) {
            const decoded: any = jwtDecode(token);
            setOrgId(decoded.org_id);
        }
    }, []);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await api.get(`/events/${id}`);
                setEvent(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    useEffect(() => {
        if (orgId) {
            fetchRelatedTasks();
        }
    }, [id, orgId]);

    const fetchRelatedTasks = async () => {
        if (!orgId) return;
        try {
            const res = await api.get(`/tasks/org/${orgId}/tasks?event_id=${id}`);
            setRelatedTasks(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
    );

    if (!event) return <div className="p-8 text-center text-slate-500">Event not found</div>;

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <Link href="/dashboard" className="text-slate-500 hover:text-indigo-600 text-sm inline-flex items-center gap-1 transition-colors">
                    <ArrowLeft size={14} />
                    Back to Dashboard
                </Link>
                <button
                    onClick={() => setIsTaskModalOpen(true)}
                    className="flex items-center gap-2 bg-slate-900 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-600 shadow-lg shadow-slate-900/20 hover:shadow-indigo-600/30 transition-all active:scale-95"
                >
                    <Plus size={18} />
                    Create Task
                </button>
            </div>

            <article className="glass-card rounded-3xl overflow-hidden">
                {/* Header Section */}
                <div className="p-8 md:p-10 border-b border-slate-100 bg-white/40">
                    <div className="flex flex-wrap items-center gap-3 mb-6">
                        <span className="bg-indigo-50 text-indigo-700 text-sm font-bold px-3 py-1 rounded-full uppercase tracking-wide border border-indigo-100">
                            {event.event_type || 'News'}
                        </span>
                        <span className="text-slate-500 text-sm font-medium flex items-center gap-1.5">
                            <Calendar size={14} />
                            {new Date(event.created_at).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                        </span>
                        {event.confidence_level && (
                            <span className={`text-xs font-bold px-2.5 py-1 rounded-full border flex items-center gap-1 ${event.confidence_level.toLowerCase() === 'high' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                                    event.confidence_level.toLowerCase() === 'medium' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                                        'bg-slate-50 text-slate-600 border-slate-200'
                                }`}>
                                <ShieldAlert size={12} />
                                {event.confidence_level} Confidence
                            </span>
                        )}
                    </div>

                    <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6 leading-tight">
                        {event.headline_summary}
                    </h1>

                    {/* Strategic Badges */}
                    <div className="flex flex-wrap gap-2 mb-8">
                        {event.urgency && (
                            <span className={`text-xs font-bold px-3 py-1.5 rounded-lg border uppercase tracking-wide ${event.urgency.toLowerCase() === 'high' ? 'bg-rose-50 text-rose-700 border-rose-200' :
                                    event.urgency.toLowerCase() === 'medium' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                                        'bg-emerald-50 text-emerald-700 border-emerald-200'
                                }`}>
                                Urgency: {event.urgency}
                            </span>
                        )}
                        {event.time_horizon && (
                            <span className="bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold px-3 py-1.5 rounded-lg uppercase tracking-wide">
                                Horizon: {event.time_horizon.replace('_', ' ')}
                            </span>
                        )}
                        {event.importance_level && (
                            <span className="bg-violet-50 text-violet-700 border border-violet-200 text-xs font-bold px-3 py-1.5 rounded-lg uppercase tracking-wide">
                                Importance: {event.importance_level}
                            </span>
                        )}
                    </div>

                    {/* Scores Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-white/60 border border-slate-200 p-4 rounded-2xl text-center shadow-sm">
                            <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1 flex items-center justify-center gap-1">
                                <AlertTriangle size={12} /> Risk Score
                            </p>
                            <p className={`text-2xl font-bold ${event.risk_score > 70 ? 'text-rose-600' : 'text-slate-800'}`}>
                                {event.risk_score ?? 'N/A'}
                            </p>
                        </div>
                        <div className="bg-white/60 border border-slate-200 p-4 rounded-2xl text-center shadow-sm">
                            <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1 flex items-center justify-center gap-1">
                                <TrendingUp size={12} /> Opportunity
                            </p>
                            <p className="text-2xl font-bold text-emerald-600">{event.opportunity_score ?? 'N/A'}</p>
                        </div>
                        <div className="bg-white/60 border border-slate-200 p-4 rounded-2xl text-center shadow-sm">
                            <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-2 flex items-center justify-center gap-1">
                                <BarChart3 size={12} /> Sentiment
                            </p>
                            <p className="text-lg font-bold capitalize text-indigo-600 mb-2">{event.sentiment || 'Neutral'}</p>
                            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                                <div
                                    className={`h-1.5 rounded-full transition-all duration-500 ${(event.sentiment_score || 0.5) > 0.6 ? 'bg-emerald-500' :
                                        (event.sentiment_score || 0.5) < 0.4 ? 'bg-rose-500' : 'bg-slate-500'
                                        }`}
                                    style={{ width: `${(event.sentiment_score || 0.5) * 100}%` }}
                                ></div>
                            </div>
                        </div>
                        <div className="bg-white/60 border border-slate-200 p-4 rounded-2xl text-center shadow-sm">
                            <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1 flex items-center justify-center gap-1">
                                <ShieldAlert size={12} /> Threat Level
                            </p>
                            <p className="text-2xl font-bold capitalize text-orange-600">{event.threat_level || 'Low'}</p>
                        </div>
                    </div>
                </div>

                {/* Main Content */}
                <div className="p-8 md:p-10 grid grid-cols-1 lg:grid-cols-3 gap-8 md:gap-12">
                    <div className="lg:col-span-2 space-y-10">
                        <section>
                            <h3 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
                                    <Lightbulb size={18} />
                                </span>
                                Executive Summary
                            </h3>
                            <p className="text-slate-700 leading-relaxed text-lg">
                                {event.short_summary}
                            </p>
                        </section>

                        {event.key_points && event.key_points.length > 0 && (
                            <section className="bg-slate-50/80 p-6 rounded-2xl border border-slate-200/60">
                                <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                    <Target size={18} className="text-indigo-600" />
                                    Key Takeaways
                                </h3>
                                <ul className="space-y-3">
                                    {event.key_points.map((point: string, i: number) => (
                                        <li key={i} className="flex gap-3 text-slate-700">
                                            <span className="text-indigo-500 font-bold mt-1">•</span>
                                            <span className="leading-relaxed">{point}</span>
                                        </li>
                                    ))}
                                </ul>
                            </section>
                        )}

                        <section>
                            <h3 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
                                    <BarChart3 size={18} />
                                </span>
                                Detailed Analysis
                            </h3>
                            <div className="prose prose-slate max-w-none text-slate-700 whitespace-pre-wrap leading-relaxed">
                                {event.detailed_summary}
                            </div>
                        </section>

                        <section className="bg-gradient-to-br from-indigo-50 to-violet-50 p-8 rounded-2xl border border-indigo-100">
                            <h3 className="text-lg font-bold text-indigo-900 mb-3 flex items-center gap-2">
                                <Zap size={18} className="text-indigo-600" />
                                Strategic Insight
                            </h3>
                            <p className="text-indigo-800 leading-relaxed font-medium">
                                {event.strategic_insight || "No strategic insight available."}
                            </p>
                        </section>
                    </div>

                    {/* Sidebar Impacts */}
                    <div className="space-y-6">
                        {/* Related Tasks Section */}
                        <div className="bg-white/50 p-6 rounded-2xl border border-slate-200 shadow-sm">
                            <h4 className="font-bold text-slate-900 mb-4 flex items-center gap-2 text-sm uppercase tracking-wide">
                                <CheckSquare size={16} className="text-indigo-600" />
                                Related Tasks
                            </h4>
                            {relatedTasks.length > 0 ? (
                                <div className="space-y-3">
                                    {relatedTasks.map(task => (
                                        <Link
                                            key={task.id}
                                            href={`/tasks/${task.id}`}
                                            className="block p-3 bg-white rounded-xl border border-slate-100 hover:border-indigo-200 hover:shadow-md transition-all group"
                                        >
                                            <div className="text-sm font-semibold text-slate-900 truncate group-hover:text-indigo-600 transition-colors">{task.title}</div>
                                            <div className="text-xs text-slate-500 mt-1 capitalize flex items-center gap-1">
                                                <div className={`w-1.5 h-1.5 rounded-full ${task.status === 'done' ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                                                {task.status.replace('_', ' ')}
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm text-slate-500 italic mb-4">No tasks linked to this event yet.</p>
                            )}
                            <button
                                onClick={() => setIsTaskModalOpen(true)}
                                className="mt-4 w-full py-2 text-sm text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 font-semibold rounded-lg transition-colors flex items-center justify-center gap-1"
                            >
                                <Plus size={16} /> Add Task
                            </button>
                        </div>

                        <div className="bg-slate-50/80 p-6 rounded-2xl border border-slate-200/60">
                            <h4 className="font-bold text-slate-900 mb-5 border-b border-slate-200 pb-3 text-sm uppercase tracking-wide">Impact Analysis</h4>

                            <div className="space-y-5">
                                <div>
                                    <p className="text-xs text-slate-500 uppercase font-bold mb-1.5 flex items-center gap-1.5">
                                        <Globe size={12} /> Market
                                    </p>
                                    <p className="text-sm text-slate-800 font-medium leading-snug">{event.impact_on_market || 'None'}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-500 uppercase font-bold mb-1.5 flex items-center gap-1.5">
                                        <ShoppingBag size={12} /> Products
                                    </p>
                                    <p className="text-sm text-slate-800 font-medium leading-snug">{event.impact_on_products || 'None'}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-500 uppercase font-bold mb-1.5 flex items-center gap-1.5">
                                        <Users size={12} /> Competitors
                                    </p>
                                    <p className="text-sm text-slate-800 font-medium leading-snug">{event.impact_on_competitors || 'None'}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-slate-500 uppercase font-bold mb-1.5 flex items-center gap-1.5">
                                        <Users size={12} /> Customers
                                    </p>
                                    <p className="text-sm text-slate-800 font-medium leading-snug">{event.impact_on_customers || 'None'}</p>
                                </div>
                            </div>
                        </div>

                        {event.tags && event.tags.length > 0 && (
                            <div>
                                <h4 className="font-bold text-slate-900 mb-3 text-xs uppercase tracking-wide pl-1">Tags</h4>
                                <div className="flex flex-wrap gap-2">
                                    {event.tags.map((tag: string, i: number) => (
                                        <span key={i} className="bg-white border border-slate-200 text-slate-600 text-xs px-2.5 py-1 rounded-lg font-medium shadow-sm">
                                            #{tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {event.recommended_actions && (
                            <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-100">
                                <h4 className="font-bold text-emerald-900 mb-2 text-sm uppercase tracking-wide flex items-center gap-2">
                                    <CheckSquare size={16} />
                                    Recommended Actions
                                </h4>
                                <p className="text-sm text-emerald-800 leading-relaxed font-medium">{event.recommended_actions}</p>
                            </div>
                        )}
                    </div>
                </div>
            </article >

            <CreateTaskModal
                isOpen={isTaskModalOpen}
                onClose={() => setIsTaskModalOpen(false)}
                eventId={id}
                initialTitle={`Task: ${event.headline_summary}`}
                onTaskCreated={fetchRelatedTasks}
            />
        </div >
    );
}
