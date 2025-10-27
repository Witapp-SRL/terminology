import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Eye, Edit, Trash2 } from 'lucide-react';
import { conceptMapAPI } from '@/api/client';

export default function ConceptMapList() {
  const [maps, setMaps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMaps();
  }, []);

  const loadMaps = async () => {
    try {
      const response = await conceptMapAPI.list();
      setMaps(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (window.confirm(`Eliminare "${name}"?`)) {
      try {
        await conceptMapAPI.delete(id);
        loadMaps();
      } catch (error) {
        alert('Errore');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Concept Maps</h1>
        <Link to="/concept-maps/new" className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700">
          <Plus className="h-5 w-5 mr-2" />Nuovo Concept Map
        </Link>
      </div>
      {loading ? (
        <div className="bg-white rounded-lg border p-8 text-center">Caricamento...</div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Azioni</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {maps.map((cm) => (
                <tr key={cm.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium">{cm.name}</div>
                    {cm.title && <div className="text-sm text-gray-500">{cm.title}</div>}
                  </td>
                  <td className="px-6 py-4"><span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs">{cm.status}</span></td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <Link to={`/concept-maps/${cm.id}`} className="text-blue-600"><Eye className="h-4 w-4 inline" /></Link>
                    <Link to={`/concept-maps/${cm.id}/edit`} className="text-gray-600"><Edit className="h-4 w-4 inline" /></Link>
                    <button onClick={() => handleDelete(cm.id, cm.name)} className="text-red-600"><Trash2 className="h-4 w-4 inline" /></button>
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
