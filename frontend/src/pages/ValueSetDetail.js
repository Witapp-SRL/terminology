import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { valueSetAPI } from '@/api/client';

export default function ValueSetDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [valueSet, setValueSet] = useState(null);

  useEffect(() => {
    loadValueSet();
  }, [id]);

  const loadValueSet = async () => {
    try {
      const response = await valueSetAPI.get(id);
      setValueSet(response.data);
    } catch (error) {
      console.error(error);
      navigate('/value-sets');
    }
  };

  if (!valueSet) return <div>Caricamento...</div>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/value-sets')} className="inline-flex items-center text-gray-600 hover:text-gray-900">
        <ArrowLeft className="h-5 w-5 mr-2" />Torna
      </button>
      <h1 className="text-3xl font-bold">{valueSet.name}</h1>
      <div className="bg-white rounded-lg border p-6">
        <dl className="grid grid-cols-2 gap-4">
          <div><dt className="text-sm font-medium text-gray-500">URL</dt><dd className="text-sm">{valueSet.url}</dd></div>
          <div><dt className="text-sm font-medium text-gray-500">Stato</dt><dd className="text-sm">{valueSet.status}</dd></div>
          {valueSet.description && <div className="col-span-2"><dt className="text-sm font-medium text-gray-500">Descrizione</dt><dd className="text-sm">{valueSet.description}</dd></div>}
        </dl>
      </div>
    </div>
  );
}
