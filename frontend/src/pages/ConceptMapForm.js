import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { conceptMapAPI } from '@/api/client';

export default function ConceptMapForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    url: '',
    name: '',
    title: '',
    status: 'draft',
    description: ''
  });

  useEffect(() => {
    if (id) loadMap();
  }, [id]);

  const loadMap = async () => {
    try {
      const response = await conceptMapAPI.get(id);
      setFormData(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (id) {
        await conceptMapAPI.update(id, formData);
      } else {
        await conceptMapAPI.create(formData);
      }
      navigate('/concept-maps');
    } catch (error) {
      alert('Errore');
    }
  };

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/concept-maps')} className="inline-flex items-center text-gray-600">
        <ArrowLeft className="h-5 w-5 mr-2" />Torna
      </button>
      <h1 className="text-3xl font-bold">{id ? 'Modifica' : 'Nuovo'} Concept Map</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white rounded-lg border p-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">URL *</label>
              <input required type="text" value={formData.url} onChange={(e) => setFormData({...formData, url: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Nome *</label>
              <input required type="text" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
            </div>
          </div>
        </div>
        <div className="flex justify-end space-x-3">
          <button type="button" onClick={() => navigate('/concept-maps')} className="px-4 py-2 border rounded-md">Annulla</button>
          <button type="submit" className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700">
            <Save className="h-5 w-5 mr-2" />{id ? 'Salva' : 'Crea'}
          </button>
        </div>
      </form>
    </div>
  );
}
