import React, { useState, useEffect } from 'react';
import { Users, Shield, UserX, UserCheck, Edit2 } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadUsers();
  }, [roleFilter, statusFilter]);

  const loadUsers = async () => {
    try {
      const params = new URLSearchParams();
      if (roleFilter) params.append('role', roleFilter);
      if (statusFilter) params.append('is_active', statusFilter);
      
      const response = await axios.get(`${API_URL}/api/admin/users?${params}`);
      setUsers(response.data.users);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async (userId, newRole) => {
    try {
      await axios.put(`${API_URL}/api/admin/users/${userId}/role`, null, {
        params: { role: newRole }
      });
      loadUsers();
    } catch (error) {
      alert('Errore: ' + (error.response?.data?.detail || 'Aggiornamento fallito'));
    }
  };

  const handleDeactivate = async (userId, username) => {
    if (!window.confirm(`Disattivare l'utente ${username}?`)) return;
    
    try {
      await axios.delete(`${API_URL}/api/admin/users/${userId}`);
      loadUsers();
    } catch (error) {
      alert('Errore: ' + (error.response?.data?.detail || 'Disattivazione fallita'));
    }
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      clinician: 'bg-blue-100 text-blue-800',
      researcher: 'bg-green-100 text-green-800',
      user: 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  if (loading) return <div className="p-6">Caricamento...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestione Utenti</h1>
          <p className="mt-2 text-gray-600">Amministra utenti e permessi del sistema</p>
        </div>
        <div className="text-sm text-gray-500">
          Totale utenti: {total}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ruolo</label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tutti i ruoli</option>
              <option value="admin">Admin</option>
              <option value="clinician">Clinician</option>
              <option value="researcher">Researcher</option>
              <option value="user">User</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stato</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tutti</option>
              <option value="true">Attivi</option>
              <option value="false">Disattivati</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Utente
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Ruolo
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Stato
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Ultimo Accesso
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Azioni
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{user.username}</div>
                    {user.full_name && (
                      <div className="text-sm text-gray-500">{user.full_name}</div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {user.email}
                </td>
                <td className="px-6 py-4">
                  <select
                    value={user.role}
                    onChange={(e) => handleUpdateRole(user.id, e.target.value)}
                    className={`text-xs px-2 py-1 rounded-full font-medium border-0 ${getRoleBadgeColor(user.role)}`}
                  >
                    <option value="user">User</option>
                    <option value="clinician">Clinician</option>
                    <option value="researcher">Researcher</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {user.is_active ? (
                      <><UserCheck className="h-3 w-3 mr-1" />Attivo</>
                    ) : (
                      <><UserX className="h-3 w-3 mr-1" />Disattivato</>
                    )}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {user.last_login ? new Date(user.last_login).toLocaleString('it-IT') : 'Mai'}
                </td>
                <td className="px-6 py-4 text-right text-sm font-medium">
                  {user.is_active && (
                    <button
                      onClick={() => handleDeactivate(user.id, user.username)}
                      className="text-red-600 hover:text-red-900 inline-flex items-center"
                      title="Disattiva utente"
                    >
                      <UserX className="h-4 w-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  Nessun utente trovato
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
        <div className="flex">
          <Shield className="h-5 w-5 text-blue-400 mr-3" />
          <div>
            <h3 className="text-sm font-medium text-blue-800">Ruoli Disponibili</h3>
            <div className="mt-2 text-sm text-blue-700 space-y-1">
              <p><strong>Admin:</strong> Accesso completo al sistema, gestione utenti e client OAuth2</p>
              <p><strong>Clinician:</strong> Accesso a risorse cliniche con permessi di lettura/scrittura</p>
              <p><strong>Researcher:</strong> Accesso in sola lettura per ricerca e analisi</p>
              <p><strong>User:</strong> Accesso base alle funzionalità del sistema</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
