import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { valueSetAPI, codeSystemAPI } from '@/api/client';

export default function ValueSetForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [codeSystems, setCodeSystems] = useState([]);
  const [formData, setFormData] = useState({
    url: '',
    name: '',
    title: '',
    status: 'draft',
    description: '',
    compose: { include: [{ system: '', concept: [] }] }
  });

  useEffect(() => {
    loadCodeSystems();
    if (id) loadValueSet();
  }, [id]);

  const loadCodeSystems = async () => {
    try {
      const response = await codeSystemAPI.list();
      setCodeSystems(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadValueSet = async () => {
    try {
      const response = await valueSetAPI.get(id);
      setFormData(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (id) {
        await valueSetAPI.update(id, formData);
      } else {
        await valueSetAPI.create(formData);
      }
      navigate('/value-sets');
    } catch (error) {
      alert('Errore durante il salvataggio');
    }
  };

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/value-sets')} className="inline-flex items-center text-gray-600">
        <ArrowLeft className="h-5 w-5 mr-2" />Torna
      </button>
      <h1 className="text-3xl font-bold">{id ? 'Modifica' : 'Nuovo'} Value Set</h1>
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
            <div>
              <label className="block text-sm font-medium mb-1">Titolo</label>
              <input type="text" value={formData.title} onChange={(e) => setFormData({...formData, title: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Stato</label>
              <select value={formData.status} onChange={(e) => setFormData({...formData, status: e.target.value})} className="w-full px-3 py-2 border rounded-md">
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="retired">Retired</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Descrizione</label>
              <textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} rows={3} className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Code System</label>
              <select value={formData.compose.include[0]?.system || ''} onChange={(e) => setFormData({...formData, compose: {include: [{system: e.target.value}]}})} className="w-full px-3 py-2 border rounded-md">
                <option value="">Seleziona un code system</option>
                {codeSystems.map(cs => <option key={cs.id} value={cs.url}>{cs.name}</option>)}
              </select>
            </div>
          </div>
        </div>
        <div className="flex justify-end space-x-3">
          <button type="button" onClick={() => navigate('/value-sets')} className="px-4 py-2 border rounded-md">Annulla</button>
          <button type="submit" className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
            <Save className="h-5 w-5 mr-2" />{id ? 'Salva' : 'Crea'}
          </button>
        </div>
      </form>
    </div>
  );
}
