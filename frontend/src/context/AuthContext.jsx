import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, getToken, setToken, removeToken } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const data = await api.getMe();
      setUser(data.user);
    } catch (err) {
      if (err.status === 401) {
        // Stored token is invalid or expired; clear it cleanly
        removeToken();
        setUser(null);
      } else {
        // Server unreachable or transient error
        console.warn('Authentication check failed:', err.message || err);
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = async (email, password) => {
    const data = await api.login({ email, password });
    setToken(data.token);
    setUser(data.user);
    return data;
  };

  const register = async (fullName, email, password, confirmPassword) => {
    const data = await api.register({
      full_name: fullName,
      email,
      password,
      confirm_password: confirmPassword
    });
    setToken(data.token);
    setUser(data.user);
    return data;
  };

  const adminLogin = async (email, password) => {
    const data = await api.adminLogin({ email, password });
    setToken(data.token);
    setUser(data.user);
    return data;
  };

  const logout = () => {
    removeToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      adminLogin,
      logout,
      refreshUser: fetchUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
