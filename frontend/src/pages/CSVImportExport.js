import React, { useState } from 'react';
import { Upload, Download, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import client from '@/api/client';

export default function CSVImportExport() {
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setImporting(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await client.post(
        '/CodeSystem/import-csv',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setImporting(false);
    }
  };

  const handleExport = async (id) => {
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/CodeSystem/${id}/export-csv`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `codesystem-${id}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6" data-testid="csv-import-export">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Import/Export CSV</h1>
        <p className="mt-2 text-gray-600">Importa ed esporta CodeSystems da file CSV</p>
      </div>

      {/* Import Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <Upload className="h-6 w-6 text-blue-600 mr-2" />
          <h2 className="text-lg font-semibold">Importa CSV</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-600 mb-3">
              Formato CSV richiesto: <code className="bg-gray-100 px-2 py-1 rounded">code,display,definition</code>
            </p>
            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer hover:bg-gray-50">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <FileText className="h-10 w-10 text-gray-400 mb-2" />
                <p className="text-sm text-gray-600">
                  {importing ? 'Importazione in corso...' : 'Clicca per selezionare il file CSV'}
                </p>
              </div>
              <input
                type="file"
                className="hidden"
                accept=".csv"
                onChange={handleImport}
                disabled={importing}
                data-testid="csv-file-input"
              />
            </label>
          </div>

          {result && (
            <div className="flex items-start p-4 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-green-900">{result.message}</p>
                <p className="text-sm text-green-700 mt-1">ID: {result.id}</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-start p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
              <p className="text-sm text-red-900">{error}</p>
            </div>
          )}
        </div>
      </div>

      {/* Export Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start">
          <Download className="h-6 w-6 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Esporta CSV</h3>
            <p className="text-blue-700 mb-3">
              Per esportare un CodeSystem in formato CSV, vai alla pagina di dettaglio del CodeSystem
              e clicca sul pulsante di export.
            </p>
            <p className="text-sm text-blue-600">
              Oppure usa l'endpoint: <code className="bg-blue-100 px-2 py-1 rounded">/api/CodeSystem/[id]/export-csv</code>
            </p>
          </div>
        </div>
      </div>

      {/* CSV Template */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-3">Template CSV di Esempio</h3>
        <div className="bg-gray-50 p-4 rounded border border-gray-200 font-mono text-sm overflow-x-auto">
          <pre>
code,display,definition
DX001,Hypertension,High blood pressure
DX002,Diabetes,Metabolic disorder
DX003,Asthma,Chronic respiratory condition
          </pre>
        </div>
        <button
          onClick={() => {
            const csv = 'code,display,definition\nDX001,Hypertension,High blood pressure\nDX002,Diabetes,Metabolic disorder\nDX003,Asthma,Chronic respiratory condition';
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'template.csv';
            link.click();
          }}
          className="mt-3 inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm"
        >
          <Download className="h-4 w-4 mr-2" />
          Scarica Template
        </button>
      </div>
    </div>
  );
}
