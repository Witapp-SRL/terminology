import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { codeSystemAPI } from '@/api/client';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function CodeSystemList() {
  const [codeSystems, setCodeSystems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showInactive, setShowInactive] = useState(false);

  useEffect(() => {
    loadCodeSystems();
  }, [showInactive]);

  const loadCodeSystems = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/CodeSystem?include_inactive=${showInactive}`);
      setCodeSystems(response.data);
    } catch (error) {
      console.error('Error loading code systems:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (window.confirm(`Sei sicuro di voler eliminare permanentemente "${name}"?`)) {
      try {
        await codeSystemAPI.delete(id);
        loadCodeSystems();
      } catch (error) {
        console.error('Error deleting code system:', error);
        alert('Errore durante l\'eliminazione');
      }
    }
  };

  const handleDeactivate = async (id, name) => {
    if (window.confirm(`Vuoi disattivare "${name}"?`)) {
      try {
        await axios.post(`${API_URL}/api/CodeSystem/${id}/deactivate`);
        loadCodeSystems();
      } catch (error) {
        console.error('Error deactivating code system:', error);
        alert('Errore durante la disattivazione');
      }
    }
  };

  const handleActivate = async (id, name) => {
    if (window.confirm(`Vuoi riattivare "${name}"?`)) {
      try {
        await axios.post(`${API_URL}/api/CodeSystem/${id}/activate`);
        loadCodeSystems();
      } catch (error) {
        console.error('Error activating code system:', error);
        alert('Errore durante la riattivazione');
      }
    }
  };

  const filteredCodeSystems = codeSystems.filter(cs => {
    const matchesSearch = !searchTerm || 
      cs.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cs.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cs.url?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = !statusFilter || cs.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6" data-testid="code-system-list">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" data-testid="page-title">Code Systems</h1>
          <p className="mt-2 text-gray-600">Gestisci i sistemi di codifica e le terminologie</p>
        </div>
        <Link
          to="/code-systems/new"
          data-testid="create-new-button"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-5 w-5 mr-2" />
          Nuovo Code System
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Cerca per nome, titolo o URL..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="search-input"
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            data-testid="status-filter"
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Tutti gli stati</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="retired">Retired</option>
          </select>
          <label className="flex items-center px-4 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Mostra disattivati</span>
          </label>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500">Caricamento...</p>
        </div>
      ) : filteredCodeSystems.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500">Nessun code system trovato</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200" data-testid="code-systems-table">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nome / Titolo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  URL
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Versione
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stato
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Concetti
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Azioni
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredCodeSystems.map((cs) => (
                <tr key={cs.id} data-testid={`code-system-row-${cs.id}`} className={`hover:bg-gray-50 ${!cs.active ? 'bg-gray-100 opacity-60' : ''}`}>
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {cs.name}
                        {!cs.active && <span className="ml-2 text-xs text-red-600">(Disattivato)</span>}
                      </div>
                      {cs.title && <div className="text-sm text-gray-500">{cs.title}</div>}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={cs.url}>
                    {cs.url}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {cs.version || '-'}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      cs.status === 'active' ? 'bg-green-100 text-green-800' :
                      cs.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {cs.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {cs.count || 0}
                  </td>
                  <td className="px-6 py-4 text-right text-sm font-medium space-x-2">
                    <Link
                      to={`/code-systems/${cs.id}`}
                      className="text-blue-600 hover:text-blue-900 inline-flex items-center"
                      title="Visualizza"
                    >
                      <Eye className="h-4 w-4" />
                    </Link>
                    {cs.active && (
                      <>
                        <Link
                          to={`/code-systems/${cs.id}/edit`}
                          className="text-yellow-600 hover:text-yellow-900 inline-flex items-center"
                          title="Modifica"
                        >
                          <Edit className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => handleDeactivate(cs.id, cs.name)}
                          className="text-orange-600 hover:text-orange-900 inline-flex items-center"
                          title="Disattiva"
                        >
                          <ToggleLeft className="h-4 w-4" />
                        </button>
                      </>
                    )}
                    {!cs.active && (
                      <button
                        onClick={() => handleActivate(cs.id, cs.name)}
                        className="text-green-600 hover:text-green-900 inline-flex items-center"
                        title="Riattiva"
                      >
                        <ToggleRight className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(cs.id, cs.name)}
                      className="text-red-600 hover:text-red-900 inline-flex items-center"
                      title="Elimina permanentemente"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
