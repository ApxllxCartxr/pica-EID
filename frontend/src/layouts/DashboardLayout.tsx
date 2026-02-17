import { useState } from 'react';
import { NavLink, Outlet, Link } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import { authService } from '../features/auth/authService';
import {
    LayoutDashboard,
    Users,
    Shield,
    FileText,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    Globe,
    Building,
} from 'lucide-react';

const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/roles', icon: Shield, label: 'Roles' },
    { to: '/domains', icon: Globe, label: 'Divisions' },
    { to: '/divisions', icon: Building, label: 'Domains' },
    { to: '/audit', icon: FileText, label: 'Audit' },
    { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function DashboardLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const { username, logout } = useAuth();

    const handleLogout = async () => {
        await authService.logout();
        logout();
    };

    return (
        <div className="flex h-screen overflow-hidden bg-background">
            {/* Sidebar */}
            <aside
                className={`relative flex flex-col border-r border-white/5 bg-slate-950/80 backdrop-blur-xl transition-all duration-300 ${sidebarOpen ? 'w-64' : 'w-20'
                    }`}
            >
                {/* Logo */}
                <div className="flex h-16 items-center gap-3 px-6 border-b border-white/5">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                        <span className="text-white font-bold text-sm">P</span>
                    </div>
                    {sidebarOpen && (
                        <span className="text-lg font-bold text-white tracking-wide">PRISMID</span>
                    )}
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-6 px-3 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                                    ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                                }`
                            }
                        >
                            <item.icon className="h-5 w-5 flex-shrink-0" />
                            {sidebarOpen && <span>{item.label}</span>}
                        </NavLink>
                    ))}
                </nav>

                {/* User section */}
                <div className="border-t border-white/5 p-4">
                    {sidebarOpen && (
                        <p className="text-xs text-slate-500 mb-2 truncate">Logged in as</p>
                    )}
                    <div className="flex items-center gap-3">
                        <Link to="/profile" className="flex items-center gap-3 flex-1 min-w-0 group">
                            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 group-hover:ring-2 ring-indigo-500/50 transition-all">
                                <span className="text-xs font-bold text-white">
                                    {username?.charAt(0).toUpperCase() || 'U'}
                                </span>
                            </div>
                            {sidebarOpen && (
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-slate-200 truncate group-hover:text-white transition-colors">{username}</p>
                                </div>
                            )}
                        </Link>
                        <button
                            onClick={handleLogout}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                            title="Logout"
                        >
                            <LogOut className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                {/* Toggle button */}
                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="absolute -right-3 top-20 h-6 w-6 rounded-full border border-white/10 bg-slate-900 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                >
                    {sidebarOpen ? <ChevronLeft className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                </button>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
