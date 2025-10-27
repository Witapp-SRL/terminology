import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import '@/App.css';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import CodeSystemList from '@/pages/CodeSystemList';
import CodeSystemDetail from '@/pages/CodeSystemDetail';
import CodeSystemForm from '@/pages/CodeSystemForm';
import ValueSetList from '@/pages/ValueSetList';
import ValueSetDetail from '@/pages/ValueSetDetail';
import ValueSetForm from '@/pages/ValueSetForm';
import ConceptMapList from '@/pages/ConceptMapList';
import ConceptMapDetail from '@/pages/ConceptMapDetail';
import ConceptMapForm from '@/pages/ConceptMapForm';
import OperationsTester from '@/pages/OperationsTester';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          
          {/* CodeSystem routes */}
          <Route path="code-systems" element={<CodeSystemList />} />
          <Route path="code-systems/new" element={<CodeSystemForm />} />
          <Route path="code-systems/:id" element={<CodeSystemDetail />} />
          <Route path="code-systems/:id/edit" element={<CodeSystemForm />} />
          
          {/* ValueSet routes */}
          <Route path="value-sets" element={<ValueSetList />} />
          <Route path="value-sets/new" element={<ValueSetForm />} />
          <Route path="value-sets/:id" element={<ValueSetDetail />} />
          <Route path="value-sets/:id/edit" element={<ValueSetForm />} />
          
          {/* ConceptMap routes */}
          <Route path="concept-maps" element={<ConceptMapList />} />
          <Route path="concept-maps/new" element={<ConceptMapForm />} />
          <Route path="concept-maps/:id" element={<ConceptMapDetail />} />
          <Route path="concept-maps/:id/edit" element={<ConceptMapForm />} />
          
          {/* Operations Tester */}
          <Route path="operations" element={<OperationsTester />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
