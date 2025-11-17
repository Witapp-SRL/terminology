import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Plus, X, ChevronDown, ChevronRight } from 'lucide-react';
import { codeSystemAPI } from '@/api/client';

// Componente per renderizzare un singolo concetto (con supporto ricorsivo per la gerarchia)
function ConceptItem({ concept, path, updateConcept, removeConcept, addConcept, level }) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = concept.concept && concept.concept.length > 0;
  
  return (
    <div className={`${level > 0 ? 'ml-6 border-l-2 border-blue-200 pl-4' : ''}`}>
      <div className="p-3 border border-gray-200 rounded-md bg-white mb-2">
        <div className="flex items-start gap-2">
          {/* Toggle per espandere/collassare i child */}
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className={`mt-2 ${hasChildren ? 'text-blue-600' : 'text-gray-300 cursor-default'}`}
            disabled={!hasChildren}
          >
            {hasChildren ? (
              expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
            ) : (
              <div className="h-4 w-4" />
            )}
          </button>

          {/* Campi del concetto */}
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-2">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Codice *</label>
              <input
                type="text"
                required
                value={concept.code || ''}
                onChange={(e) => updateConcept(path, 'code', e.target.value)}
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                placeholder="CODE001"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Display</label>
              <input
                type="text"
                value={concept.display || ''}
                onChange={(e) => updateConcept(path, 'display', e.target.value)}
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                placeholder="Nome del concetto"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Definizione</label>
              <input
                type="text"
                value={concept.definition || ''}
                onChange={(e) => updateConcept(path, 'definition', e.target.value)}
                className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                placeholder="Descrizione"
              />
            </div>
          </div>

          {/* Azioni */}
          <div className="flex flex-col gap-1 mt-5">
            <button
              type="button"
              onClick={() => addConcept(path)}
              className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
              title="Aggiungi sotto-concetto"
            >
              <Plus className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => removeConcept(path)}
              className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
              title="Rimuovi concetto"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Children badge */}
        {hasChildren && (
          <div className="mt-2 ml-6">
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
              {concept.concept.length} sotto-concetto/i
            </span>
          </div>
        )}
      </div>

      {/* Render children ricorsivamente */}
      {expanded && hasChildren && (
        <div className="mt-1">
          {concept.concept.map((childConcept, index) => (
            <ConceptItem
              key={index}
              concept={childConcept}
              path={[...path, index]}
              updateConcept={updateConcept}
              removeConcept={removeConcept}
              addConcept={addConcept}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

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

  const addConcept = (parentPath = null) => {
    const newConcept = { code: '', display: '', definition: '', concept: [] };
    
    if (parentPath === null) {
      // Aggiungi al root
      setFormData({
        ...formData,
        concept: [...formData.concept, newConcept]
      });
    } else {
      // Aggiungi come child
      const newConcepts = [...formData.concept];
      let parent = newConcepts;
      
      // Naviga fino al parent
      for (let i = 0; i < parentPath.length; i++) {
        parent = parent[parentPath[i]].concept;
      }
      
      parent.push(newConcept);
      setFormData({ ...formData, concept: newConcepts });
    }
  };

  const updateConcept = (path, field, value) => {
    const newConcepts = [...formData.concept];
    let concept = newConcepts;
    
    // Naviga fino al concetto
    for (let i = 0; i < path.length - 1; i++) {
      concept = concept[path[i]].concept;
    }
    
    concept[path[path.length - 1]][field] = value;
    setFormData({ ...formData, concept: newConcepts });
  };

  const removeConcept = (path) => {
    const newConcepts = [...formData.concept];
    
    if (path.length === 1) {
      // Rimuovi dal root
      setFormData({
        ...formData,
        concept: formData.concept.filter((_, i) => i !== path[0])
      });
    } else {
      // Rimuovi da nested
      let parent = newConcepts;
      for (let i = 0; i < path.length - 1; i++) {
        parent = parent[path[i]].concept;
      }
      parent.splice(path[path.length - 1], 1);
      setFormData({ ...formData, concept: newConcepts });
    }
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
            <h2 className="text-lg font-semibold">Concetti (Gerarchici)</h2>
            <button
              type="button"
              onClick={() => addConcept(null)}
              className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              <Plus className="h-4 w-4 mr-1" />
              Aggiungi Concetto Root
            </button>
          </div>
          <div className="space-y-2">
            {formData.concept.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">
                Nessun concetto aggiunto. Clicca "Aggiungi Concetto Root" per iniziare.
              </p>
            )}
            {formData.concept.map((concept, index) => (
              <ConceptItem 
                key={index}
                concept={concept}
                path={[index]}
                updateConcept={updateConcept}
                removeConcept={removeConcept}
                addConcept={addConcept}
                level={0}
              />
            ))}
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
