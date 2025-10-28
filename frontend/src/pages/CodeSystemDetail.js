import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Calendar, Globe, Database, Download } from 'lucide-react';
import { codeSystemAPI } from '@/api/client';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function CodeSystemDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [codeSystem, setCodeSystem] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCodeSystem();
  }, [id]);

  const loadCodeSystem = async () => {
    try {
      setLoading(true);
      const response = await codeSystemAPI.get(id);
      setCodeSystem(response.data);
    } catch (error) {
      console.error('Error loading code system:', error);
      alert('Errore nel caricamento del code system');
      navigate('/code-systems');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/CodeSystem/${id}/export-csv`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${codeSystem.name}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Errore durante l\'export');
    }
  };

  const renderConcepts = (concepts, level = 0) => {
    if (!concepts || concepts.length === 0) return null;

    return (
      <div className={level > 0 ? 'ml-6 border-l-2 border-gray-200 pl-4' : ''}>
        {concepts.map((concept, index) => (
          <div key={index} className="py-3 border-b border-gray-100 last:border-0">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <code className="px-2 py-1 bg-gray-100 rounded text-sm font-mono">
                    {concept.code}
                  </code>
                  {concept.display && (
                    <span className="text-sm font-medium text-gray-900">{concept.display}</span>
                  )}
                </div>
                {concept.definition && (
                  <p className="mt-1 text-sm text-gray-600">{concept.definition}</p>
                )}
                {concept.property && concept.property.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {concept.property.map((prop, idx) => (
                      <span key={idx} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                        {prop.code}: {prop.valueCode || prop.valueString || prop.valueInteger}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            {concept.concept && renderConcepts(concept.concept, level + 1)}
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Caricamento...</p>
      </div>
    );
  }

  if (!codeSystem) return null;

  return (
    <div className="space-y-6" data-testid="code-system-detail">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/code-systems')}
          data-testid="back-button"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Torna alla lista
        </button>
        <h1 className="text-3xl font-bold text-gray-900" data-testid="code-system-name">{codeSystem.name}</h1>
        {codeSystem.title && <p className="mt-2 text-xl text-gray-600">{codeSystem.title}</p>}
      </div>

      {/* Metadata */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Informazioni</h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500 flex items-center">
              <Globe className="h-4 w-4 mr-2" />
              URL
            </dt>
            <dd className="mt-1 text-sm text-gray-900 break-all">{codeSystem.url}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Versione</dt>
            <dd className="mt-1 text-sm text-gray-900">{codeSystem.version || 'Non specificata'}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Stato</dt>
            <dd className="mt-1">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                codeSystem.status === 'active' ? 'bg-green-100 text-green-800' :
                codeSystem.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {codeSystem.status}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500 flex items-center">
              <Calendar className="h-4 w-4 mr-2" />
              Data
            </dt>
            <dd className="mt-1 text-sm text-gray-900">
              {codeSystem.date ? new Date(codeSystem.date).toLocaleDateString('it-IT') : 'Non specificata'}
            </dd>
          </div>
          {codeSystem.publisher && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Editore</dt>
              <dd className="mt-1 text-sm text-gray-900">{codeSystem.publisher}</dd>
            </div>
          )}
          <div>
            <dt className="text-sm font-medium text-gray-500 flex items-center">
              <Database className="h-4 w-4 mr-2" />
              Numero di Concetti
            </dt>
            <dd className="mt-1 text-sm text-gray-900">
              {codeSystem.count || codeSystem.concept?.length || 0}
            </dd>
          </div>
        </dl>
        {codeSystem.description && (
          <div className="mt-4">
            <dt className="text-sm font-medium text-gray-500">Descrizione</dt>
            <dd className="mt-1 text-sm text-gray-900">{codeSystem.description}</dd>
          </div>
        )}
      </div>

      {/* Properties */}
      {codeSystem.property && codeSystem.property.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Proprietà</h2>
          <div className="space-y-2">
            {codeSystem.property.map((prop, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                <code className="px-2 py-1 bg-white rounded text-sm font-mono border border-gray-200">
                  {prop.code}
                </code>
                <span className="text-sm text-gray-600">{prop.type}</span>
                {prop.description && (
                  <span className="text-sm text-gray-500">- {prop.description}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Concepts */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Concetti</h2>
        {codeSystem.concept && codeSystem.concept.length > 0 ? (
          <div className="space-y-2">{renderConcepts(codeSystem.concept)}</div>
        ) : (
          <p className="text-gray-500 text-sm">Nessun concetto definito</p>
        )}
      </div>
    </div>
  );
}
