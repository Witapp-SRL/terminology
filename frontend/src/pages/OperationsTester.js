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
          {/* CodeSystem Operations */}
          {operation === 'lookup' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">System URL *</label>
                <input type="text" value={params.system || ''} onChange={(e) => setParams({...params, system: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/CodeSystem/diagnosis-codes" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Code *</label>
                <input type="text" value={params.code || ''} onChange={(e) => setParams({...params, code: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="DX001" />
              </div>
            </>
          )}
          {operation === 'validate-code-cs' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">System URL *</label>
                <input type="text" value={params.system || ''} onChange={(e) => setParams({...params, system: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/CodeSystem/diagnosis-codes" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Code *</label>
                <input type="text" value={params.code || ''} onChange={(e) => setParams({...params, code: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="DX001" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Display (opzionale)</label>
                <input type="text" value={params.display || ''} onChange={(e) => setParams({...params, display: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="Diagnosis Display" />
              </div>
            </>
          )}
          {operation === 'subsumes' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">System URL *</label>
                <input type="text" value={params.system || ''} onChange={(e) => setParams({...params, system: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://snomed.info/sct" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Code A *</label>
                <input type="text" value={params.codeA || ''} onChange={(e) => setParams({...params, codeA: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="Primo codice" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Code B *</label>
                <input type="text" value={params.codeB || ''} onChange={(e) => setParams({...params, codeB: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="Secondo codice" />
              </div>
            </>
          )}
          {operation === 'find-matches-cs' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">System URL (opzionale)</label>
                <input type="text" value={params.system || ''} onChange={(e) => setParams({...params, system: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/CodeSystem/diagnosis-codes" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Valore da cercare</label>
                <input type="text" value={params.value || ''} onChange={(e) => setParams({...params, value: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="es. diabetes" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Proprietà (opzionale)</label>
                <select value={params.property || ''} onChange={(e) => setParams({...params, property: e.target.value})} className="w-full px-3 py-2 border rounded-md">
                  <option value="">Tutte</option>
                  <option value="display">Display</option>
                  <option value="code">Code</option>
                  <option value="definition">Definition</option>
                </select>
              </div>
              <div>
                <label className="flex items-center">
                  <input type="checkbox" checked={params.exact || false} onChange={(e) => setParams({...params, exact: e.target.checked})} className="mr-2" />
                  Match esatto
                </label>
              </div>
            </>
          )}
          
          {/* ValueSet Operations */}
          {operation === 'expand' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">ValueSet URL *</label>
                <input type="text" value={params.url || ''} onChange={(e) => setParams({...params, url: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/ValueSet/chronic-conditions" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Filter (opzionale)</label>
                <input type="text" value={params.filter || ''} onChange={(e) => setParams({...params, filter: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="Filtra per testo" />
              </div>
            </>
          )}
          {operation === 'validate-code-vs' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">ValueSet URL *</label>
                <input type="text" value={params.url || ''} onChange={(e) => setParams({...params, url: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/ValueSet/chronic-conditions" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Code *</label>
                <input type="text" value={params.code || ''} onChange={(e) => setParams({...params, code: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="CODE001" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">System (opzionale)</label>
                <input type="text" value={params.system || ''} onChange={(e) => setParams({...params, system: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/CodeSystem/..." />
              </div>
            </>
          )}
          {operation === 'compose' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">CodeSystem URLs da includere * (separati da virgola)</label>
                <textarea 
                  value={params.include || ''} 
                  onChange={(e) => setParams({...params, include: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} 
                  className="w-full px-3 py-2 border rounded-md" 
                  rows="3"
                  placeholder="http://example.org/fhir/CodeSystem/system1,&#10;http://example.org/fhir/CodeSystem/system2"
                />
                <p className="text-xs text-gray-500 mt-1">Inserisci gli URL dei CodeSystem separati da virgola</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">CodeSystem URLs da escludere (opzionale, separati da virgola)</label>
                <input 
                  type="text" 
                  value={params.exclude ? params.exclude.join(', ') : ''} 
                  onChange={(e) => setParams({...params, exclude: e.target.value.split(',').map(s => s.trim()).filter(Boolean)})} 
                  className="w-full px-3 py-2 border rounded-md" 
                  placeholder="http://example.org/fhir/CodeSystem/system-to-exclude" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Filter (opzionale)</label>
                <input type="text" value={params.filter || ''} onChange={(e) => setParams({...params, filter: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="Filtra concetti per testo" />
              </div>
            </>
          )}
          {operation === 'find-matches-vs' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">ValueSet URL (opzionale)</label>
                <input type="text" value={params.url || ''} onChange={(e) => setParams({...params, url: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/ValueSet/..." />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Valore da cercare</label>
                <input type="text" value={params.value || ''} onChange={(e) => setParams({...params, value: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="es. chronic disease" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Proprietà (opzionale)</label>
                <select value={params.property || ''} onChange={(e) => setParams({...params, property: e.target.value})} className="w-full px-3 py-2 border rounded-md">
                  <option value="">Tutte</option>
                  <option value="display">Display</option>
                  <option value="code">Code</option>
                  <option value="definition">Definition</option>
                </select>
              </div>
            </>
          )}
          
          {/* ConceptMap Operations */}
          {operation === 'translate' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-1">ConceptMap URL (opzionale)</label>
                <input type="text" value={params.url || ''} onChange={(e) => setParams({...params, url: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/ConceptMap/..." />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Source Code *</label>
                <input type="text" value={params.code || ''} onChange={(e) => setParams({...params, code: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="SOURCE_CODE" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Source System *</label>
                <input type="text" value={params.system || ''} onChange={(e) => setParams({...params, system: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/CodeSystem/source" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Target System (opzionale)</label>
                <input type="text" value={params.target || ''} onChange={(e) => setParams({...params, target: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="http://example.org/fhir/CodeSystem/target" />
              </div>
            </>
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
