import React, { useState, useEffect } from 'react';
import { Plus, Key, Trash2, Edit, Eye, EyeOff, Copy, RefreshCw } from 'lucide-react';
import api from '@/lib/axios';

export default function OAuth2Clients() {
  const [clients, setClients] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newClientSecret, setNewClientSecret] = useState(null);

  useEffect(() => {
    loadClients();
  }, []);

  const loadClients = async () => {
    try {
      const response = await api.get('/oauth2/clients');
      setClients(response.data.clients);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Error loading clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClient = async (formData) => {
    try {
      const response = await api.post('/oauth2/clients', formData);
      setNewClientSecret(response.data);
      loadClients();
      setShowCreateModal(false);
    } catch (error) {
      alert('Errore: ' + (error.response?.data?.detail || 'Creazione fallita'));
    }
  };

  const handleResetSecret = async (clientId) => {
    if (!window.confirm('Resettare il client secret? Il vecchio secret non funzionerà più.')) return;
    
    try {
      const response = await api.post(`/oauth2/clients/${clientId}/reset-secret`);
      setNewClientSecret(response.data);
    } catch (error) {
      alert('Errore: ' + (error.response?.data?.detail || 'Reset fallito'));
    }
  };

  const handleDeactivate = async (clientId) => {
    if (!window.confirm('Disattivare questo client?')) return;
    
    try {
      await api.delete(`/oauth2/clients/${clientId}`);
      loadClients();
    } catch (error) {
      alert('Errore: ' + (error.response?.data?.detail || 'Disattivazione fallita'));
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copiato negli appunti!');
  };

  if (loading) return <div className="p-6">Caricamento...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">OAuth2 Clients</h1>
          <p className="mt-2 text-gray-600">Gestisci applicazioni client per l'accesso alle API FHIR</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="h-5 w-5 mr-2" />
          Nuovo Client
        </button>
      </div>

      {/* New Client Secret Modal */}
      {newClientSecret && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              ⚠️ Salva le Credenziali Client
            </h2>
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
              <p className="text-sm text-yellow-800">
                <strong>ATTENZIONE:</strong> Il client secret sarà mostrato solo ora. Salvalo in un luogo sicuro!
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Client ID</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={newClientSecret.client_id}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 font-mono text-sm"
                  />
                  <button
                    onClick={() => copyToClipboard(newClientSecret.client_id)}
                    className="px-3 py-2 bg-gray-200 rounded-md hover:bg-gray-300"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Client Secret</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={newClientSecret.client_secret}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 font-mono text-sm"
                  />
                  <button
                    onClick={() => copyToClipboard(newClientSecret.client_secret)}
                    className="px-3 py-2 bg-gray-200 rounded-md hover:bg-gray-300"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setNewClientSecret(null)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Ho salvato le credenziali
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Client Modal */}
      {showCreateModal && (
        <ClientFormModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateClient}
        />
      )}

      {/* Clients Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Client Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Client ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Scopes
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Last Used
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Azioni
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {clients.map((client) => (
              <tr key={client.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{client.client_name}</div>
                    {client.description && (
                      <div className="text-sm text-gray-500">{client.description}</div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {client.client_id}
                  </code>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {client.scopes.slice(0, 3).map((scope, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {scope}
                      </span>
                    ))}
                    {client.scopes.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{client.scopes.length - 3} more
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    client.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {client.is_active ? 'Attivo' : 'Disattivato'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {client.last_used ? new Date(client.last_used).toLocaleString('it-IT') : 'Mai'}
                </td>
                <td className="px-6 py-4 text-right text-sm font-medium space-x-2">
                  <button
                    onClick={() => handleResetSecret(client.client_id)}
                    className="text-yellow-600 hover:text-yellow-900 inline-flex items-center"
                    title="Reset Secret"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDeactivate(client.client_id)}
                    className="text-red-600 hover:text-red-900 inline-flex items-center"
                    title="Disattiva"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
            {clients.length === 0 && (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  Nessun client OAuth2 configurato
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Client Form Modal Component
function ClientFormModal({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    client_name: '',
    description: '',
    redirect_uris: [''],
    grant_types: ['client_credentials'],
    scopes: []
  });
  const [availableScopes, setAvailableScopes] = useState([]);

  useEffect(() => {
    loadScopes();
  }, []);

  const loadScopes = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/oauth2/scopes`);
      setAvailableScopes(response.data.scopes);
    } catch (error) {
      console.error('Error loading scopes:', error);
    }
  };

  const addRedirectUri = () => {
    setFormData({
      ...formData,
      redirect_uris: [...formData.redirect_uris, '']
    });
  };

  const updateRedirectUri = (index, value) => {
    const newUris = [...formData.redirect_uris];
    newUris[index] = value;
    setFormData({ ...formData, redirect_uris: newUris });
  };

  const removeRedirectUri = (index) => {
    setFormData({
      ...formData,
      redirect_uris: formData.redirect_uris.filter((_, i) => i !== index)
    });
  };

  const toggleScope = (scopeName) => {
    const newScopes = formData.scopes.includes(scopeName)
      ? formData.scopes.filter(s => s !== scopeName)
      : [...formData.scopes, scopeName];
    setFormData({ ...formData, scopes: newScopes });
  };

  const toggleGrantType = (grantType) => {
    const newTypes = formData.grant_types.includes(grantType)
      ? formData.grant_types.filter(t => t !== grantType)
      : [...formData.grant_types, grantType];
    setFormData({ ...formData, grant_types: newTypes });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  // Group scopes by context
  const groupedScopes = availableScopes.reduce((acc, scope) => {
    const context = scope.name.split('/')[0] || 'other';
    if (!acc[context]) acc[context] = [];
    acc[context].push(scope);
    return acc;
  }, {});

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Nuovo Client OAuth2</h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome Client *
            </label>
            <input
              type="text"
              required
              value={formData.client_name}
              onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              placeholder="My FHIR Application"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrizione
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              placeholder="Descrizione dell'applicazione..."
            />
          </div>

          {/* Redirect URIs */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Redirect URIs *
            </label>
            {formData.redirect_uris.map((uri, index) => (
              <div key={index} className="flex items-center gap-2 mb-2">
                <input
                  type="url"
                  required
                  value={uri}
                  onChange={(e) => updateRedirectUri(index, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder="https://myapp.com/callback"
                />
                {formData.redirect_uris.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeRedirectUri(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={addRedirectUri}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              + Aggiungi Redirect URI
            </button>
          </div>

          {/* Grant Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Grant Types *
            </label>
            <div className="space-y-2">
              {['authorization_code', 'client_credentials', 'refresh_token'].map(type => (
                <label key={type} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.grant_types.includes(type)}
                    onChange={() => toggleGrantType(type)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">{type}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Scopes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Scopes FHIR *
            </label>
            <div className="border border-gray-300 rounded-md p-4 max-h-64 overflow-y-auto">
              {Object.entries(groupedScopes).map(([context, scopes]) => (
                <div key={context} className="mb-4">
                  <h4 className="font-semibold text-sm text-gray-700 mb-2 capitalize">
                    {context} Scopes
                  </h4>
                  <div className="space-y-1 ml-4">
                    {scopes.map(scope => (
                      <label key={scope.name} className="flex items-start">
                        <input
                          type="checkbox"
                          checked={formData.scopes.includes(scope.name)}
                          onChange={() => toggleScope(scope.name)}
                          className="mt-1 mr-2"
                        />
                        <div>
                          <span className="text-sm font-mono text-gray-900">{scope.name}</span>
                          <p className="text-xs text-gray-500">{scope.description}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Seleziona almeno uno scope. Scopes con * sono wildcards.
            </p>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Annulla
            </button>
            <button
              type="submit"
              disabled={formData.scopes.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Crea Client
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
