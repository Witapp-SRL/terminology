import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
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
import CSVImportExport from '@/pages/CSVImportExport';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import AuditLog from '@/pages/AuditLog';
import AdminDashboard from '@/pages/AdminDashboard';
import UserManagement from '@/pages/UserManagement';
import OAuth2Clients from '@/pages/OAuth2Clients';
import ActiveTokens from '@/pages/ActiveTokens';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';

// Protected Route wrapper
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div className="flex items-center justify-center h-screen">Caricamento...</div>;
  }
  
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

// Admin Route wrapper
function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="flex items-center justify-center h-screen">Caricamento...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (!user.is_admin && user.role !== 'admin') {
    return <Navigate to="/" replace />;
  }
  
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Dashboard />} />
            <Route path="csv" element={<CSVImportExport />} />
            <Route path="audit-log" element={<AuditLog />} />
            
            {/* Admin routes */}
            <Route path="admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
            <Route path="admin/users" element={<AdminRoute><UserManagement /></AdminRoute>} />
            <Route path="admin/oauth2-clients" element={<AdminRoute><OAuth2Clients /></AdminRoute>} />
            <Route path="admin/tokens" element={<AdminRoute><ActiveTokens /></AdminRoute>} />
            
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
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
