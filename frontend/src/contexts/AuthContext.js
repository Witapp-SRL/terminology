import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Remove trailing /api if present, then add it
const cleanBackendUrl = API_URL.replace(/\/api\/?$/, '');
const BASE_URL = `${cleanBackendUrl}/api`;

const AuthContext = createContext(null);

// Create a separate axios instance for auth to avoid circular dependencies
const authAPI = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  // Set axios default header when token changes
  useEffect(() => {
    if (token) {
      authAPI.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      loadUser();
    } else {
      delete authAPI.defaults.headers.common['Authorization'];
      setLoading(false);
    }
  }, [token]);

  const loadUser = async () => {
    try {
      const response = await authAPI.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to load user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await authAPI.post('/auth/login', {
        username,
        password
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      authAPI.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Load user data before returning
      const userResponse = await authAPI.get('/auth/me');
      setUser(userResponse.data);
      setToken(access_token);
      setLoading(false);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Login failed'
      };
    }
  };

  const register = async (username, email, password, full_name) => {
    try {
      await authAPI.post('/auth/register', {
        username,
        email,
        password,
        full_name
      });
      
      // Auto-login after registration
      return await login(username, password);
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete authAPI.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      isAuthenticated: !!user,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
