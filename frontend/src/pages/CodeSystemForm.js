import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Plus, X } from 'lucide-react';
import { codeSystemAPI } from '@/api/client';

export default function CodeSystemForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  
  const [formData, setFormData] = useState({
    url: '',
    version: '',
    name: '',
    title: '',
    status: 'draft',
    publisher: '',
    description: '',
    caseSensitive: true,
    content: 'complete',
    concept: []  // Inizializza sempre come array vuoto
  });
  
  const [loading, setLoading] = useState(isEdit);

  useEffect(() => {
    if (isEdit) {
      loadCodeSystem();
    }
  }, [id]);

  const loadCodeSystem = async () => {
    try {
      const response = await codeSystemAPI.get(id);
      setFormData(response.data);
    } catch (error) {
      console.error('Error loading code system:', error);
      alert('Errore nel caricamento');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEdit) {
        await codeSystemAPI.update(id, formData);
      } else {
        await codeSystemAPI.create(formData);
      }
      navigate('/code-systems');
    } catch (error) {
      console.error('Error saving code system:', error);
      alert('Errore durante il salvataggio');
    }
  };

  const addConcept = () => {
    setFormData({
      ...formData,
      concept: [...formData.concept, { code: '', display: '', definition: '' }]
    });
  };

  const updateConcept = (index, field, value) => {
    const newConcepts = [...formData.concept];
    newConcepts[index][field] = value;
    setFormData({ ...formData, concept: newConcepts });
  };

  const removeConcept = (index) => {
    setFormData({
      ...formData,
      concept: formData.concept.filter((_, i) => i !== index)
    });
  };

  if (loading) return <div className="p-6">Caricamento...</div>;

  return (
    <div className="space-y-6" data-testid="code-system-form">
      <div>
        <button onClick={() => navigate('/code-systems')} className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4">
          <ArrowLeft className="h-5 w-5 mr-2" />
          Torna alla lista
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {isEdit ? 'Modifica Code System' : 'Nuovo Code System'}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Informazioni di Base</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL * <span className="text-gray-500">(univoco)</span>
              </label>
              <input
                type="text"
                required
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="http://example.org/fhir/CodeSystem/my-codes"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Versione</label>
              <input
                type="text"
                value={formData.version}
                onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="1.0.0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="MyCodeSystem"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Titolo</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="My Code System"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stato *</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="retired">Retired</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Publisher</label>
              <input
                type="text"
                value={formData.publisher}
                onChange={(e) => setFormData({ ...formData, publisher: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="Organization Name"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                placeholder="Descrizione del code system..."
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Concetti</h2>
            <button
              type="button"
              onClick={addConcept}
              className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              <Plus className="h-4 w-4 mr-1" />
              Aggiungi Concetto
            </button>
          </div>
          <div className="space-y-4">
            {formData.concept.map((concept, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-md relative">
                <button
                  type="button"
                  onClick={() => removeConcept(index)}
                  className="absolute top-2 right-2 text-red-600 hover:text-red-800"
                >
                  <X className="h-5 w-5" />
                </button>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pr-8">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Codice *</label>
                    <input
                      type="text"
                      required
                      value={concept.code}
                      onChange={(e) => updateConcept(index, 'code', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                      placeholder="CODE001"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Display</label>
                    <input
                      type="text"
                      value={concept.display}
                      onChange={(e) => updateConcept(index, 'display', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                      placeholder="Nome del concetto"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Definizione</label>
                    <input
                      type="text"
                      value={concept.definition}
                      onChange={(e) => updateConcept(index, 'definition', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                      placeholder="Descrizione del concetto"
                    />
                  </div>
                </div>
              </div>
            ))}
            {formData.concept.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">
                Nessun concetto aggiunto. Clicca "Aggiungi Concetto" per iniziare.
              </p>
            )}
          </div>
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate('/code-systems')}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Annulla
          </button>
          <button
            type="submit"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Save className="h-5 w-5 mr-2" />
            {isEdit ? 'Salva Modifiche' : 'Crea Code System'}
          </button>
        </div>
      </form>
    </div>
  );
}
