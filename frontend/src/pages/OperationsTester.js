import React, { useState } from 'react';
import { Play } from 'lucide-react';
import { codeSystemAPI, valueSetAPI, conceptMapAPI } from '@/api/client';

export default function OperationsTester() {
  const [operation, setOperation] = useState('lookup');
  const [params, setParams] = useState({ system: '', code: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runOperation = async () => {
    setLoading(true);
    setResult(null);
    try {
      let response;
      switch (operation) {
        case 'lookup':
          response = await codeSystemAPI.lookup(params);
          break;
        case 'validate-code-cs':
          response = await codeSystemAPI.validateCode(params);
          break;
        case 'subsumes':
          response = await codeSystemAPI.subsumes(params);
          break;
        case 'find-matches-cs':
          response = await codeSystemAPI.findMatches(params);
          break;
        case 'expand':
          response = await valueSetAPI.expand({ url: params.url });
          break;
        case 'validate-code-vs':
          response = await valueSetAPI.validateCode(params);
          break;
        case 'compose':
          response = await valueSetAPI.compose(params);
          break;
        case 'find-matches-vs':
          response = await valueSetAPI.findMatches(params);
          break;
        case 'translate':
          response = await conceptMapAPI.translate(params);
          break;
        default:
          response = { data: 'Operazione non implementata' };
      }
      setResult(response.data);
    } catch (error) {
      setResult({ error: error.message, details: error.response?.data });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Operations Tester</h1>
      <div className="bg-white rounded-lg border p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Operazione</label>
            <select value={operation} onChange={(e) => setOperation(e.target.value)} className="w-full px-3 py-2 border rounded-md">
              <optgroup label="CodeSystem Operations">
                <option value="lookup">$lookup - Cerca dettagli di un codice</option>
                <option value="validate-code-cs">$validate-code - Valida un codice</option>
                <option value="subsumes">$subsumes - Test relazione gerarchica</option>
                <option value="find-matches-cs">$find-matches - Cerca codici per proprietà</option>
              </optgroup>
              <optgroup label="ValueSet Operations">
                <option value="expand">$expand - Espandi ValueSet</option>
                <option value="validate-code-vs">$validate-code - Valida codice in ValueSet</option>
                <option value="compose">$compose - Componi ValueSet da CodeSystems</option>
                <option value="find-matches-vs">$find-matches - Cerca in ValueSet</option>
              </optgroup>
              <optgroup label="ConceptMap Operations">
                <option value="translate">$translate - Traduci codice tra sistemi</option>
              </optgroup>
            </select>
          </div>
          {operation === 'lookup' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">System</label>
                <input type="text" value={params.system} onChange={(e) => setParams({...params, system: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/CodeSystem/diagnosis-codes" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Code</label>
                <input type="text" value={params.code} onChange={(e) => setParams({...params, code: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="DX001" />
              </div>
            </>
          )}
          {operation === 'validate-code' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">System</label>
                <input type="text" value={params.system} onChange={(e) => setParams({...params, system: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Code</label>
                <input type="text" value={params.code} onChange={(e) => setParams({...params, code: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
              </div>
            </>
          )}
          {operation === 'expand' && (
            <div>
              <label className="block text-sm font-medium mb-1">ValueSet URL</label>
              <input type="text" value={params.url} onChange={(e) => setParams({...params, url: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/ValueSet/chronic-conditions" />
            </div>
          )}
          <button onClick={runOperation} disabled={loading} className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
            <Play className="h-5 w-5 mr-2" />
            {loading ? 'Esecuzione...' : 'Esegui Operazione'}
          </button>
        </div>
      </div>
      {result && (
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-3">Risultato</h2>
          <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto max-h-96">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
