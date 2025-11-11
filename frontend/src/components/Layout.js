import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Activity, Database, GitBranch, Map, TestTube2, Menu, FileSpreadsheet, History, LogOut, User, Shield, Users, Key } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Activity },
  { name: 'Code Systems', href: '/code-systems', icon: Database },
  { name: 'Value Sets', href: '/value-sets', icon: GitBranch },
  { name: 'Concept Maps', href: '/concept-maps', icon: Map },
  { name: 'Operations Tester', href: '/operations', icon: TestTube2 },
  { name: 'Import/Export CSV', href: '/csv', icon: FileSpreadsheet },
  { name: 'Audit Log', href: '/audit-log', icon: History },
];

const adminNavigation = [
  { name: 'Admin Dashboard', href: '/admin', icon: Shield },
  { name: 'Gestione Utenti', href: '/admin/users', icon: Users },
  { name: 'OAuth2 Clients', href: '/admin/oauth2-clients', icon: Key },
  { name: 'Token Attivi', href: '/admin/tokens', icon: Shield },
];

export default function Layout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const { user, logout } = useAuth();
  
  const isAdmin = user?.is_admin || user?.role === 'admin';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 px-4 py-3">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-md text-gray-600 hover:bg-gray-100"
          data-testid="mobile-menu-button"
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>

      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="px-6 py-6 border-b border-gray-200">
            <h1 className="text-xl font-bold text-gray-900" data-testid="app-title">
              FHIR Terminology
            </h1>
            <p className="text-sm text-gray-500 mt-1">Service Management</p>
          </div>

          {/* User info */}
          {user && (
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center text-white font-semibold ${
                    isAdmin ? 'bg-purple-500' : 'bg-blue-500'
                  }`}>
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className="ml-3 flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {user.full_name || user.username}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {user.email}
                  </p>
                  {isAdmin && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 mt-1">
                      <Shield className="h-3 w-3 mr-1" />
                      Admin
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto" data-testid="navigation">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                (item.href !== '/' && location.pathname.startsWith(item.href));
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                  className={cn(
                    "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-600"
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  )}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className={cn("mr-3 h-5 w-5", isActive ? "text-blue-600" : "text-gray-400")} />
                  {item.name}
                </Link>
              );
            })}
            
            {/* Admin Section */}
            {isAdmin && (
              <>
                <div className="pt-4 pb-2">
                  <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Amministrazione
                  </p>
                </div>
                {adminNavigation.map((item) => {
                  const isActive = location.pathname === item.href || 
                    (item.href !== '/admin' && location.pathname.startsWith(item.href));
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={cn(
                        "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                        isActive
                          ? "bg-purple-50 text-purple-600"
                          : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                      )}
                      onClick={() => setSidebarOpen(false)}
                    >
                      <item.icon className={cn("mr-3 h-5 w-5", isActive ? "text-purple-600" : "text-gray-400")} />
                      {item.name}
                    </Link>
                  );
                })}
              </>
            )}
            
            {/* Logout button */}
            <button
              onClick={logout}
              className="w-full flex items-center px-3 py-2 text-sm font-medium rounded-md text-red-600 hover:bg-red-50 transition-colors mt-4"
            >
              <LogOut className="mr-3 h-5 w-5" />
              Logout
            </button>
          </nav>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">Version 1.0.0</p>
            <p className="text-xs text-gray-400 mt-1">FHIR R4 Compatible</p>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="lg:pl-64 pt-16 lg:pt-0">
        <main className="p-6" data-testid="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
