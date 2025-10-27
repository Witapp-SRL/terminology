import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { conceptMapAPI } from '@/api/client';

export default function ConceptMapDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [map, setMap] = useState(null);

  useEffect(() => {
    loadMap();
  }, [id]);

  const loadMap = async () => {
    try {
      const response = await conceptMapAPI.get(id);
      setMap(response.data);
    } catch (error) {
      navigate('/concept-maps');
    }
  };

  if (!map) return <div>Caricamento...</div>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/concept-maps')} className="inline-flex items-center text-gray-600">
        <ArrowLeft className="h-5 w-5 mr-2" />Torna
      </button>
      <h1 className="text-3xl font-bold">{map.name}</h1>
      <div className="bg-white rounded-lg border p-6">
        <dl className="space-y-3">
          <div><dt className="text-sm font-medium text-gray-500">URL</dt><dd className="text-sm">{map.url}</dd></div>
          <div><dt className="text-sm font-medium text-gray-500">Stato</dt><dd className="text-sm">{map.status}</dd></div>
        </dl>
      </div>
    </div>
  );
}
