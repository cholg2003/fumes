import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Lock, AlertCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SetupPassword = () => {
  const navigate = useNavigate();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const username = localStorage.getItem('username');
  const tempPassword = localStorage.getItem('temp_password');

  useEffect(() => {
    if (!username || !tempPassword) {
      navigate('/login');
    }
  }, [username, tempPassword, navigate]);

  const validatePassword = () => {
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return false;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return false;
    }
    return true;
  };

  const handleSetupPassword = async (e) => {
    e.preventDefault();
    
    if (!validatePassword()) {
      return;
    }

    setLoading(true);

    try {
      await axios.post(`${API}/auth/setup-password`, {
        username,
        temporary_password: tempPassword,
        new_password: newPassword
      });

      toast.success('Password set successfully! Please login with your new password.');
      
      // Clear temporary data
      localStorage.removeItem('temp_password');
      localStorage.removeItem('token');
      
      // Redirect to login
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to set password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'linear-gradient(135deg, #e3f2fd 0%, #f0f4f8 100%)' }}>
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-blue-100">
          <div className="flex items-center justify-center mb-8">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-4 rounded-2xl shadow-lg">
              <Lock className="w-10 h-10 text-white" />
            </div>
          </div>
          
          <h1 className="text-3xl font-bold text-center mb-2 text-gray-800">Set Your Password</h1>
          <p className="text-center text-gray-600 mb-8">Create a secure password for your account</p>

          <div className="mb-6 p-4 bg-amber-50 rounded-lg border border-amber-200 flex gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-800">
              <p className="font-semibold mb-1">First Time Login</p>
              <p>Please set a strong password for your account. You'll use this password for future logins.</p>
            </div>
          </div>

          <form onSubmit={handleSetupPassword} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-gray-700 font-medium">Username</Label>
              <Input
                id="username"
                type="text"
                value={username}
                disabled
                className="h-11 border-gray-300 bg-gray-50"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="newPassword" className="text-gray-700 font-medium">New Password</Label>
              <Input
                id="newPassword"
                data-testid="new-password-input"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password (min 8 characters)"
                required
                className="h-11 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-gray-700 font-medium">Confirm Password</Label>
              <Input
                id="confirmPassword"
                data-testid="confirm-password-input"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
                required
                className="h-11 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div className="pt-2">
              <div className="text-xs text-gray-600 space-y-1 mb-4">
                <p className="font-semibold text-gray-700">Password Requirements:</p>
                <p>• At least 8 characters long</p>
                <p>• Use a mix of letters, numbers, and symbols</p>
              </div>

              <Button
                type="submit"
                data-testid="setup-password-button"
                disabled={loading}
                className="w-full h-11 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold rounded-lg shadow-md transition-all duration-200"
              >
                {loading ? 'Setting Password...' : 'Set Password'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SetupPassword;
