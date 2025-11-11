import React, { useState, useEffect } from 'react';
import { Users, Key, Shield, Database, Activity, TrendingUp } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/admin/dashboard`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6">Caricamento statistiche...</div>;
  }

  if (!stats) {
    return <div className="p-6 text-red-600">Errore nel caricamento delle statistiche</div>;
  }

  const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Amministratore</h1>
        <p className="mt-2 text-gray-600">Benvenuto, {user?.full_name || user?.username}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={Users}
          title="Utenti Totali"
          value={stats.users.total}
          subtitle={`${stats.users.active} attivi`}
          color="bg-blue-500"
        />
        
        <StatCard
          icon={Key}
          title="OAuth2 Clients"
          value={stats.oauth2_clients.total}
          subtitle={`${stats.oauth2_clients.active} attivi`}
          color="bg-purple-500"
        />
        
        <StatCard
          icon={Shield}
          title="Token Attivi"
          value={stats.tokens.active}
          subtitle={`${stats.tokens.revoked} revocati`}
          color="bg-green-500"
        />
        
        <StatCard
          icon={Activity}
          title="Audit Log (24h)"
          value={stats.audit_logs.last_24h}
          subtitle={`${stats.audit_logs.total} totali`}
          color="bg-orange-500"
        />
      </div>

      {/* Users by Role */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Utenti per Ruolo</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(stats.users.by_role).map(([role, count]) => (
            <div key={role} className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{count}</p>
              <p className="text-sm text-gray-600 capitalize">{role}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Resources Stats */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Database className="h-5 w-5 mr-2" />
          Risorse FHIR
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border-l-4 border-blue-500 pl-4">
            <p className="text-sm text-gray-600">Code Systems</p>
            <p className="text-2xl font-bold text-gray-900">{stats.resources.code_systems}</p>
            <p className="text-xs text-gray-500 mt-1">
              {stats.resources.code_systems_active} attivi
            </p>
          </div>
          
          <div className="border-l-4 border-green-500 pl-4">
            <p className="text-sm text-gray-600">Value Sets</p>
            <p className="text-2xl font-bold text-gray-900">{stats.resources.value_sets}</p>
          </div>
          
          <div className="border-l-4 border-purple-500 pl-4">
            <p className="text-sm text-gray-600">Concept Maps</p>
            <p className="text-2xl font-bold text-gray-900">{stats.resources.concept_maps}</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Azioni Rapide</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/admin/users"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Users className="h-8 w-8 text-blue-500 mr-3" />
            <div>
              <p className="font-medium text-gray-900">Gestione Utenti</p>
              <p className="text-sm text-gray-500">Gestisci ruoli e permessi</p>
            </div>
          </a>
          
          <a
            href="/admin/oauth2-clients"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Key className="h-8 w-8 text-purple-500 mr-3" />
            <div>
              <p className="font-medium text-gray-900">OAuth2 Clients</p>
              <p className="text-sm text-gray-500">Gestisci applicazioni client</p>
            </div>
          </a>
          
          <a
            href="/admin/tokens"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Shield className="h-8 w-8 text-green-500 mr-3" />
            <div>
              <p className="font-medium text-gray-900">Token Attivi</p>
              <p className="text-sm text-gray-500">Monitora e revoca token</p>
            </div>
          </a>
        </div>
      </div>

      {/* Security Info */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
        <div className="flex">
          <Shield className="h-5 w-5 text-blue-400 mr-3 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-blue-800">Sistema di Sicurezza FHIR</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>✅ OAuth2 e SMART on FHIR implementati</p>
              <p>✅ Scopes granulari per controllo accessi</p>
              <p>✅ Audit trail completo di tutte le operazioni</p>
              <p>✅ Token JWT con scadenza automatica</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
