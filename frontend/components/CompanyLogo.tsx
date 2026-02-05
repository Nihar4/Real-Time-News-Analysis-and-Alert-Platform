'use client';

import { useState } from 'react';
import { Building2 } from 'lucide-react';

interface CompanyLogoProps {
    slug: string;
    name: string;
    size?: number;
    className?: string;
}

export default function CompanyLogo({ slug, name, size = 40, className = '' }: CompanyLogoProps) {
    const [error, setError] = useState(false);
    const logoUrl = `https://img.logo.dev/${slug}.com?token=pk_E5EbUIoJR4S5GQZj2arTfw`;

    if (error) {
        return (
            <div
                className={`bg-white border border-slate-100 flex items-center justify-center rounded-lg ${className}`}
                style={{ width: size, height: size }}
            >
                <Building2 size={size * 0.5} className="text-slate-300" />
            </div>
        );
    }

    return (
        <div
            className={`bg-white relative overflow-hidden rounded-lg flex items-center justify-center ${className}`}
            style={{ width: size, height: size }}
        >
            <img
                src={logoUrl}
                alt={`${name} logo`}
                className="w-full h-full object-contain p-1"
                onError={() => setError(true)}
            />
        </div>
    );
}
