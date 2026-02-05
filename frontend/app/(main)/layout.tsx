import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";

export default function MainLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <div className="flex h-screen p-4 gap-4">
            {/* Sidebar Container */}
            <aside className="hidden md:block w-64 shrink-0 h-full">
                <Sidebar />
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col h-full gap-4 min-w-0">
                {/* Navbar Container */}
                <header className="h-16 shrink-0">
                    <Navbar />
                </header>

                {/* Page Content Container */}
                <main className="flex-1 glass-panel rounded-3xl overflow-hidden relative">
                    <div className="absolute inset-0 overflow-y-auto p-6 md:p-8 scroll-smooth">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
