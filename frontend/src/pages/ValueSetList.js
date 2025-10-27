import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Eye, Edit, Trash2 } from 'lucide-react';
import { valueSetAPI } from '@/api/client';

export default function ValueSetList() {
  const [valueSets, setValueSets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadValueSets();
  }, []);

  const loadValueSets = async () => {
    try {
      const response = await valueSetAPI.list();
      setValueSets(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (window.confirm(`Eliminare "${name}"?`)) {
      try {
        await valueSetAPI.delete(id);
        loadValueSets();
      } catch (error) {
        alert('Errore durante l\'eliminazione');
      }
    }
  };

  const filtered = valueSets.filter(vs =>
    !searchTerm ||
    vs.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    vs.title?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6" data-testid="value-set-list">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Value Sets</h1>
        <Link to="/value-sets/new" className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
          <Plus className="h-5 w-5 mr-2" />
          Nuovo Value Set
        </Link>
      </div>

      <div className="bg-white rounded-lg border p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Cerca..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-md"
          />
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg border p-8 text-center">Caricamento...</div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">URL</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Azioni</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((vs) => (
                <tr key={vs.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium">{vs.name}</div>
                    {vs.title && <div className="text-sm text-gray-500">{vs.title}</div>}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{vs.url}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      vs.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {vs.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <Link to={`/value-sets/${vs.id}`} className="text-blue-600"><Eye className="h-4 w-4 inline" /></Link>
                    <Link to={`/value-sets/${vs.id}/edit`} className="text-gray-600"><Edit className="h-4 w-4 inline" /></Link>
                    <button onClick={() => handleDelete(vs.id, vs.name)} className="text-red-600"><Trash2 className="h-4 w-4 inline" /></button>
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
