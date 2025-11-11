import React, { useState, useEffect } from 'react';
import { Key, Trash2, Filter, Clock } from 'lucide-react';
import api from '@/lib/axios';

export default function ActiveTokens() {
  const [tokens, setTokens] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [clientFilter, setClientFilter] = useState('');
  const [clients, setClients] = useState([]);

  useEffect(() => {
    loadClients();
    loadTokens();
  }, [clientFilter]);

  const loadClients = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/oauth2/clients`);
      setClients(response.data.clients);
    } catch (error) {
      console.error('Error loading clients:', error);
    }
  };

  const loadTokens = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (clientFilter) params.append('client_id', clientFilter);
      
      const response = await axios.get(`${API_URL}/api/oauth2/tokens?${params}`);
      setTokens(response.data.tokens);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Error loading tokens:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeToken = async (tokenId) => {
    if (!window.confirm('Revocare questo token?')) return;
    
    try {
      await axios.delete(`${API_URL}/api/oauth2/tokens/${tokenId}`);
      loadTokens();
    } catch (error) {
      alert('Errore: ' + (error.response?.data?.detail || 'Revoca fallita'));
    }
  };

  const formatTimeRemaining = (expiresAt) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diff = expiry - now;
    
    if (diff <= 0) return 'Scaduto';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days} giorni`;
    }
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  if (loading) return <div className="p-6">Caricamento...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Token Attivi</h1>
          <p className="mt-2 text-gray-600">Gestisci i token OAuth2 attivi nel sistema</p>
        </div>
        <div className="text-sm text-gray-500">
          Token attivi: {total}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-semibold">Filtri</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client
            </label>
            <select
              value={clientFilter}
              onChange={(e) => setClientFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Tutti i client</option>
              {clients.map(client => (
                <option key={client.id} value={client.client_id}>
                  {client.client_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tokens Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Client
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Scopes
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Creato
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Scade tra
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Azioni
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tokens.map((token) => (
              <tr key={token.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {token.client_id}
                  </code>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {token.user_id ? (
                    <span className="inline-flex items-center">
                      <Users className="h-4 w-4 mr-1" />
                      User
                    </span>
                  ) : (
                    <span className="text-gray-400 italic">System</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1 max-w-xs">
                    {token.scopes.slice(0, 2).map((scope, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {scope}
                      </span>
                    ))}
                    {token.scopes.length > 2 && (
                      <span className="text-xs text-gray-500">
                        +{token.scopes.length - 2}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {new Date(token.created_at).toLocaleDateString('it-IT')}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center text-sm text-gray-700">
                    <Clock className="h-4 w-4 mr-1 text-gray-400" />
                    {formatTimeRemaining(token.expires_at)}
                  </div>
                </td>
                <td className="px-6 py-4 text-right text-sm font-medium">
                  <button
                    onClick={() => handleRevokeToken(token.id)}
                    className="text-red-600 hover:text-red-900 inline-flex items-center"
                    title="Revoca token"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
            {tokens.length === 0 && (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  Nessun token attivo
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Info Box */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex">
          <Key className="h-5 w-5 text-yellow-400 mr-3" />
          <div>
            <h3 className="text-sm font-medium text-yellow-800">Gestione Token</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>I token OAuth2 vengono automaticamente invalidati alla scadenza.</p>
              <p className="mt-1">Revocando un token, tutte le richieste con quel token falliranno immediatamente.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
