import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PrintBill from './pages/PrintBill';
import Admin from './pages/Admin';
import AdminCRUD from './pages/AdminCRUD';
import SetupPassword from './pages/SetupPassword';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/setup-password" element={<SetupPassword />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/crud" element={<AdminCRUD />} />
        <Route path="/print/:billId" element={<PrintBill />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;