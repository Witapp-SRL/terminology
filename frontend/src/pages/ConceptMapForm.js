import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Plus, X, ArrowRight } from 'lucide-react';
import { conceptMapAPI } from '@/api/client';

export default function ConceptMapForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    url: '',
    name: '',
    title: '',
    status: 'draft',
    description: '',
    sourceCanonical: '',
    targetCanonical: '',
    group: []
  });

  useEffect(() => {
    if (id) loadMap();
  }, [id]);

  const loadMap = async () => {
    try {
      const response = await conceptMapAPI.get(id);
      setFormData({
        ...response.data,
        group: response.data.group || []
      });
    } catch (error) {
      console.error(error);
      alert('Errore nel caricamento');
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
      console.error('Error saving:', error);
      alert('Errore durante il salvataggio');
    }
  };

  const addGroup = () => {
    setFormData({
      ...formData,
      group: [...formData.group, {
        source: formData.sourceCanonical || '',
        target: formData.targetCanonical || '',
        element: []
      }]
    });
  };

  const removeGroup = (groupIndex) => {
    setFormData({
      ...formData,
      group: formData.group.filter((_, i) => i !== groupIndex)
    });
  };

  const updateGroup = (groupIndex, field, value) => {
    const newGroups = [...formData.group];
    newGroups[groupIndex][field] = value;
    setFormData({ ...formData, group: newGroups });
  };

  const addElement = (groupIndex) => {
    const newGroups = [...formData.group];
    if (!newGroups[groupIndex].element) {
      newGroups[groupIndex].element = [];
    }
    newGroups[groupIndex].element.push({
      code: '',
      display: '',
      target: [{
        code: '',
        display: '',
        equivalence: 'equivalent'
      }]
    });
    setFormData({ ...formData, group: newGroups });
  };

  const removeElement = (groupIndex, elementIndex) => {
    const newGroups = [...formData.group];
    newGroups[groupIndex].element = newGroups[groupIndex].element.filter((_, i) => i !== elementIndex);
    setFormData({ ...formData, group: newGroups });
  };

  const updateElement = (groupIndex, elementIndex, field, value) => {
    const newGroups = [...formData.group];
    newGroups[groupIndex].element[elementIndex][field] = value;
    setFormData({ ...formData, group: newGroups });
  };

  const updateTarget = (groupIndex, elementIndex, targetIndex, field, value) => {
    const newGroups = [...formData.group];
    newGroups[groupIndex].element[elementIndex].target[targetIndex][field] = value;
    setFormData({ ...formData, group: newGroups });
  };

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/concept-maps')} className="inline-flex items-center text-gray-600 hover:text-gray-900">
        <ArrowLeft className="h-5 w-5 mr-2" />Torna alla lista
      </button>
      <h1 className="text-3xl font-bold">{id ? 'Modifica' : 'Nuovo'} Concept Map</h1>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Informazioni di Base */}
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">Informazioni di Base</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">URL *</label>
              <input 
                required 
                type="text" 
                value={formData.url} 
                onChange={(e) => setFormData({...formData, url: e.target.value})} 
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-purple-500"
                placeholder="http://example.org/fhir/ConceptMap/my-map"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Nome *</label>
              <input 
                required 
                type="text" 
                value={formData.name} 
                onChange={(e) => setFormData({...formData, name: e.target.value})} 
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-purple-500"
                placeholder="MyConceptMap"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Titolo</label>
              <input 
                type="text" 
                value={formData.title || ''} 
                onChange={(e) => setFormData({...formData, title: e.target.value})} 
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-purple-500"
                placeholder="My Concept Map"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Stato *</label>
              <select 
                value={formData.status} 
                onChange={(e) => setFormData({...formData, status: e.target.value})} 
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-purple-500"
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="retired">Retired</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Descrizione</label>
              <textarea 
                value={formData.description || ''} 
                onChange={(e) => setFormData({...formData, description: e.target.value})} 
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-purple-500"
                rows="3"
                placeholder="Descrizione del concept map..."
              />
            </div>
          </div>
        </div>

        {/* Source e Target Systems */}
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">Sistemi Source e Target</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Source CodeSystem URL</label>
              <input 
                type="text" 
                value={formData.sourceCanonical || ''} 
                onChange={(e) => setFormData({...formData, sourceCanonical: e.target.value})} 
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-purple-500"
                placeholder="http://example.org/fhir/CodeSystem/source"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Target CodeSystem URL</label>
              <input 
                type="text" 
                value={formData.targetCanonical || ''} 
                onChange={(e) => setFormData({...formData, targetCanonical: e.target.value})} 
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-purple-500"
                placeholder="http://example.org/fhir/CodeSystem/target"
              />
            </div>
          </div>
        </div>

        {/* Mapping Groups */}
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Mapping Groups</h2>
            <button 
              type="button" 
              onClick={addGroup} 
              className="inline-flex items-center px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm"
            >
              <Plus className="h-4 w-4 mr-1" />Aggiungi Gruppo
            </button>
          </div>

          {formData.group.length === 0 && (
            <p className="text-gray-500 text-center py-4">Nessun gruppo di mapping. Clicca "Aggiungi Gruppo" per iniziare.</p>
          )}

          {formData.group.map((group, groupIndex) => (
            <div key={groupIndex} className="border rounded-lg p-4 mb-4 bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-gray-700">Gruppo {groupIndex + 1}</h3>
                <button 
                  type="button" 
                  onClick={() => removeGroup(groupIndex)} 
                  className="text-red-600 hover:text-red-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-xs font-medium mb-1">Source System</label>
                  <input 
                    type="text" 
                    value={group.source || ''} 
                    onChange={(e) => updateGroup(groupIndex, 'source', e.target.value)} 
                    className="w-full px-2 py-1 border rounded text-sm"
                    placeholder="URL del sistema source"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">Target System</label>
                  <input 
                    type="text" 
                    value={group.target || ''} 
                    onChange={(e) => updateGroup(groupIndex, 'target', e.target.value)} 
                    className="w-full px-2 py-1 border rounded text-sm"
                    placeholder="URL del sistema target"
                  />
                </div>
              </div>

              {/* Elements (Mappings) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Mappings</span>
                  <button 
                    type="button" 
                    onClick={() => addElement(groupIndex)} 
                    className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs hover:bg-purple-200"
                  >
                    <Plus className="h-3 w-3 mr-1" />Aggiungi Mapping
                  </button>
                </div>

                {group.element && group.element.length > 0 ? (
                  group.element.map((element, elementIndex) => (
                    <div key={elementIndex} className="bg-white border rounded p-3">
                      <div className="flex items-start gap-2">
                        {/* Source */}
                        <div className="flex-1">
                          <label className="block text-xs text-gray-600 mb-1">Source Code</label>
                          <input 
                            type="text" 
                            value={element.code || ''} 
                            onChange={(e) => updateElement(groupIndex, elementIndex, 'code', e.target.value)} 
                            className="w-full px-2 py-1 border rounded text-sm mb-1"
                            placeholder="SOURCE_CODE"
                          />
                          <input 
                            type="text" 
                            value={element.display || ''} 
                            onChange={(e) => updateElement(groupIndex, elementIndex, 'display', e.target.value)} 
                            className="w-full px-2 py-1 border rounded text-sm"
                            placeholder="Display (opzionale)"
                          />
                        </div>

                        <ArrowRight className="h-5 w-5 text-gray-400 mt-6" />

                        {/* Target */}
                        <div className="flex-1">
                          <label className="block text-xs text-gray-600 mb-1">Target Code</label>
                          <input 
                            type="text" 
                            value={element.target?.[0]?.code || ''} 
                            onChange={(e) => updateTarget(groupIndex, elementIndex, 0, 'code', e.target.value)} 
                            className="w-full px-2 py-1 border rounded text-sm mb-1"
                            placeholder="TARGET_CODE"
                          />
                          <input 
                            type="text" 
                            value={element.target?.[0]?.display || ''} 
                            onChange={(e) => updateTarget(groupIndex, elementIndex, 0, 'display', e.target.value)} 
                            className="w-full px-2 py-1 border rounded text-sm mb-1"
                            placeholder="Display (opzionale)"
                          />
                          <select 
                            value={element.target?.[0]?.equivalence || 'equivalent'} 
                            onChange={(e) => updateTarget(groupIndex, elementIndex, 0, 'equivalence', e.target.value)} 
                            className="w-full px-2 py-1 border rounded text-sm"
                          >
                            <option value="relatedto">Related To</option>
                            <option value="equivalent">Equivalent</option>
                            <option value="equal">Equal</option>
                            <option value="wider">Wider</option>
                            <option value="subsumes">Subsumes</option>
                            <option value="narrower">Narrower</option>
                            <option value="specializes">Specializes</option>
                            <option value="inexact">Inexact</option>
                            <option value="unmatched">Unmatched</option>
                            <option value="disjoint">Disjoint</option>
                          </select>
                        </div>

                        <button 
                          type="button" 
                          onClick={() => removeElement(groupIndex, elementIndex)} 
                          className="text-red-600 hover:text-red-800 mt-6"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-xs text-center py-2">Nessun mapping in questo gruppo</p>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end space-x-3">
          <button 
            type="button" 
            onClick={() => navigate('/concept-maps')} 
            className="px-4 py-2 border rounded-md hover:bg-gray-50"
          >
            Annulla
          </button>
          <button 
            type="submit" 
            className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
          >
            <Save className="h-5 w-5 mr-2" />
            {id ? 'Salva Modifiche' : 'Crea Concept Map'}
          </button>
        </div>
      </form>
    </div>
  );
}
