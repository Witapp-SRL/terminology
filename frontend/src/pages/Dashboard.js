import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Database, GitBranch, Map, Activity } from 'lucide-react';
import { codeSystemAPI, valueSetAPI, conceptMapAPI } from '@/api/client';

export default function Dashboard() {
  const [stats, setStats] = useState({
    codeSystems: 0,
    valueSets: 0,
    conceptMaps: 0,
    loading: true,
  });

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [cs, vs, cm] = await Promise.all([
        codeSystemAPI.list(),
        valueSetAPI.list(),
        conceptMapAPI.list(),
      ]);
      
      setStats({
        codeSystems: cs.data.length,
        valueSets: vs.data.length,
        conceptMaps: cm.data.length,
        loading: false,
      });
    } catch (error) {
      console.error('Error loading stats:', error);
      setStats(prev => ({ ...prev, loading: false }));
    }
  };

  const cards = [
    {
      title: 'Code Systems',
      value: stats.codeSystems,
      icon: Database,
      link: '/code-systems',
      color: 'blue',
      description: 'Define terminologies and code sets',
    },
    {
      title: 'Value Sets',
      value: stats.valueSets,
      icon: GitBranch,
      link: '/value-sets',
      color: 'green',
      description: 'Collections of codes from systems',
    },
    {
      title: 'Concept Maps',
      value: stats.conceptMaps,
      icon: Map,
      link: '/concept-maps',
      color: 'purple',
      description: 'Mappings between code systems',
    },
  ];

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900" data-testid="dashboard-title">Dashboard</h1>
        <p className="mt-2 text-gray-600">Gestione del servizio di terminologia FHIR</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card) => (
          <Link
            key={card.title}
            to={card.link}
            data-testid={`card-${card.title.toLowerCase().replace(/\s+/g, '-')}`}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">{card.title}</p>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {stats.loading ? '...' : card.value}
                </p>
                <p className="mt-2 text-sm text-gray-500">{card.description}</p>
              </div>
              <div className={`p-3 rounded-lg bg-${card.color}-50`}>
                <card.icon className={`h-6 w-6 text-${card.color}-600`} />
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Azioni Rapide</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/code-systems/new"
            data-testid="quick-action-new-codesystem"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-blue-500 hover:bg-blue-50 transition-colors"
          >
            <Database className="h-8 w-8 mx-auto text-gray-400 mb-2" />
            <p className="text-sm font-medium text-gray-700">Nuovo Code System</p>
          </Link>
          <Link
            to="/value-sets/new"
            data-testid="quick-action-new-valueset"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-green-500 hover:bg-green-50 transition-colors"
          >
            <GitBranch className="h-8 w-8 mx-auto text-gray-400 mb-2" />
            <p className="text-sm font-medium text-gray-700">Nuovo Value Set</p>
          </Link>
          <Link
            to="/concept-maps/new"
            data-testid="quick-action-new-conceptmap"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-purple-500 hover:bg-purple-50 transition-colors"
          >
            <Map className="h-8 w-8 mx-auto text-gray-400 mb-2" />
            <p className="text-sm font-medium text-gray-700">Nuovo Concept Map</p>
          </Link>
          <Link
            to="/operations"
            data-testid="quick-action-operations"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-orange-500 hover:bg-orange-50 transition-colors"
          >
            <Activity className="h-8 w-8 mx-auto text-gray-400 mb-2" />
            <p className="text-sm font-medium text-gray-700">Testa Operazioni</p>
          </Link>
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Informazioni sul Servizio</h3>
        <p className="text-blue-700 mb-4">
          Questo servizio implementa le specifiche FHIR R4 per la gestione della terminologia.
        </p>
        <ul className="space-y-2 text-sm text-blue-700">
          <li className="flex items-start">
            <span className="mr-2">✓</span>
            <span>Supporto completo per CodeSystem, ValueSet e ConceptMap</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">✓</span>
            <span>Operazioni FHIR: $expand, $lookup, $validate-code, $subsumes, $translate</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">✓</span>
            <span>API RESTful con ricerca e filtri avanzati</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
