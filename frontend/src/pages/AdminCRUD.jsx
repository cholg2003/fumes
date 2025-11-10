import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { ArrowLeft, Plus, Edit, Trash2, Building2, Users, UserPlus, UsersRound, FileText, Receipt, Printer, Ban, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RELATIONSHIPS = ['Principle', 'Spouse', 'Father', 'Mother', 'Child', 'Dependent'];
const ROLES = ['Admin', 'Finance', 'Reception'];

const AdminCRUD = () => {
  const navigate = useNavigate();
  const [hospitals, setHospitals] = useState([]);
  const [users, setUsers] = useState([]);
  const [families, setFamilies] = useState([]);
  const [members, setMembers] = useState([]);
  const [pricelists, setPricelists] = useState([]);
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(false);

  // Dialog states
  const [hospitalDialog, setHospitalDialog] = useState(false);
  const [userDialog, setUserDialog] = useState(false);
  const [familyDialog, setFamilyDialog] = useState(false);
  const [memberDialog, setMemberDialog] = useState(false);
  const [pricelistDialog, setPricelistDialog] = useState(false);

  // Forms
  const [hospitalForm, setHospitalForm] = useState({ hospital_name: '', address: '', phone: '', email: '' });
  const [userForm, setUserForm] = useState({ username: '', hospital_name: '', role: 'Billing Clerk', temporary_password: '', first_login: true });
  const [familyForm, setFamilyForm] = useState({ family_id: '', principle_member_name: '', total_allotment: '', remaining_balance: '' });
  const [memberForm, setMemberForm] = useState({ serial_number: '', family_id: '', first_name: '', middle_name: '', last_name: '', dob: '', sex: 'Male', relationship: 'Principle' });
  const [pricelistForm, setPricelistForm] = useState({ hospital_name: '', item_id: '', item_name: '', item_type: 'Service', cost: '' });

  // Edit states
  const [editMode, setEditMode] = useState({ type: '', data: null });

  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');
  const username = localStorage.getItem('username');
  const hospitalName = localStorage.getItem('hospital_name');
  
  const isSuperAdmin = username === 'superadmin';

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    if (!isSuperAdmin) {
      toast.error('Access denied. Superadmin only.');
      navigate('/dashboard');
      return;
    }
    loadData();
  }, []);

  const axiosConfig = {
    headers: { Authorization: `Bearer ${token}` }
  };

  const loadData = async () => {
    try {
      const requests = [
        axios.get(`${API}/admin/families`, axiosConfig),
        axios.get(`${API}/admin/members`, axiosConfig),
        axios.get(`${API}/admin/pricelists/all`, axiosConfig)
      ];
      
      // Claims endpoint differs based on user type
      if (isSuperAdmin) {
        requests.unshift(
          axios.get(`${API}/admin/hospitals`, axiosConfig),
          axios.get(`${API}/admin/users`, axiosConfig)
        );
        requests.push(axios.get(`${API}/admin/claims/all`, axiosConfig)); // All claims for superadmin
      } else {
        requests.push(axios.get(`${API}/bills`, axiosConfig)); // Only hospital bills
      }
      
      const responses = await Promise.all(requests);
      
      if (isSuperAdmin) {
        setHospitals(responses[0].data);
        setUsers(responses[1].data);
        setFamilies(responses[2].data);
        setMembers(responses[3].data);
        setPricelists(responses[4].data);
        setClaims(responses[5].data);
      } else {
        setFamilies(responses[0].data);
        setMembers(responses[1].data);
        setPricelists(responses[2].data);
        setClaims(responses[3].data);
        // For hospital admin, only load their hospital info
        setHospitals([{ hospital_name: hospitalName }]);
      }
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  // Hospital CRUD
  const handleHospitalSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editMode.type === 'hospital') {
        await axios.put(`${API}/admin/hospitals/${editMode.data.hospital_name}`, hospitalForm, axiosConfig);
        toast.success('Hospital updated successfully');
      } else {
        await axios.post(`${API}/admin/hospitals`, hospitalForm, axiosConfig);
        toast.success('Hospital created successfully');
      }
      setHospitalDialog(false);
      setHospitalForm({ hospital_name: '', address: '', phone: '', email: '' });
      setEditMode({ type: '', data: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleHospitalDelete = async (hospitalName) => {
    if (!window.confirm(`Delete hospital "${hospitalName}"? This will fail if the hospital has users or price lists.`)) return;
    try {
      await axios.delete(`${API}/admin/hospitals/${hospitalName}`, axiosConfig);
      toast.success('Hospital deleted successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete hospital');
    }
  };

  // User CRUD
  const handleUserSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editMode.type === 'user') {
        await axios.put(`${API}/admin/users/${editMode.data.username}`, {
          hospital_name: userForm.hospital_name,
          role: userForm.role
        }, axiosConfig);
        toast.success('User updated successfully');
      } else {
        await axios.post(`${API}/admin/users`, userForm, axiosConfig);
        toast.success('User created successfully');
      }
      setUserDialog(false);
      setUserForm({ username: '', hospital_name: '', role: 'Billing Clerk', temporary_password: '', first_login: true });
      setEditMode({ type: '', data: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUserDelete = async (username) => {
    if (!window.confirm(`Delete user "${username}"?`)) return;
    try {
      await axios.delete(`${API}/admin/users/${username}`, axiosConfig);
      toast.success('User deleted successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  // Family CRUD
  const handleFamilySubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editMode.type === 'family') {
        await axios.put(`${API}/admin/families/${editMode.data.family_id}`, {
          principle_member_name: familyForm.principle_member_name,
          total_allotment: parseFloat(familyForm.total_allotment),
          remaining_balance: parseFloat(familyForm.remaining_balance)
        }, axiosConfig);
        toast.success('Family updated successfully');
      } else {
        await axios.post(`${API}/admin/families`, {
          ...familyForm,
          total_allotment: parseFloat(familyForm.total_allotment),
          remaining_balance: parseFloat(familyForm.remaining_balance)
        }, axiosConfig);
        toast.success('Family created successfully');
      }
      setFamilyDialog(false);
      setFamilyForm({ family_id: '', principle_member_name: '', total_allotment: '', remaining_balance: '' });
      setEditMode({ type: '', data: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFamilyDelete = async (familyId) => {
    if (!window.confirm(`Delete family "${familyId}"? This will fail if the family has members or claims.`)) return;
    try {
      await axios.delete(`${API}/admin/families/${familyId}`, axiosConfig);
      toast.success('Family deleted successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete family');
    }
  };

  // Member CRUD
  const handleMemberSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editMode.type === 'member') {
        await axios.put(`${API}/admin/members/${editMode.data.serial_number}`, {
          first_name: memberForm.first_name,
          middle_name: memberForm.middle_name,
          last_name: memberForm.last_name,
          dob: memberForm.dob,
          sex: memberForm.sex,
          relationship: memberForm.relationship
        }, axiosConfig);
        toast.success('Member updated successfully');
      } else {
        await axios.post(`${API}/admin/members`, memberForm, axiosConfig);
        toast.success('Member created successfully');
      }
      setMemberDialog(false);
      setMemberForm({ serial_number: '', family_id: '', first_name: '', middle_name: '', last_name: '', dob: '', sex: 'Male', relationship: 'Principle' });
      setEditMode({ type: '', data: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleMemberDelete = async (serialNumber) => {
    if (!window.confirm(`Delete member "${serialNumber}"? This will fail if the member has claims.`)) return;
    try {
      await axios.delete(`${API}/admin/members/${serialNumber}`, axiosConfig);
      toast.success('Member deleted successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete member');
    }
  };

  // Suspend/Unsuspend handlers
  const handleFamilySuspend = async (familyId) => {
    if (!window.confirm(`Suspend family "${familyId}"? All members will be automatically suspended.`)) return;
    try {
      await axios.post(`${API}/admin/families/${familyId}/suspend`, {}, axiosConfig);
      toast.success('Family suspended successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to suspend family');
    }
  };

  const handleFamilyUnsuspend = async (familyId) => {
    if (!window.confirm(`Unsuspend family "${familyId}"? All members will be automatically unsuspended.`)) return;
    try {
      await axios.post(`${API}/admin/families/${familyId}/unsuspend`, {}, axiosConfig);
      toast.success('Family unsuspended successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to unsuspend family');
    }
  };

  const handleMemberSuspend = async (serialNumber) => {
    if (!window.confirm(`Suspend member "${serialNumber}"?`)) return;
    try {
      await axios.post(`${API}/admin/members/${serialNumber}/suspend`, {}, axiosConfig);
      toast.success('Member suspended successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to suspend member');
    }
  };

  const handleMemberUnsuspend = async (serialNumber) => {
    if (!window.confirm(`Unsuspend member "${serialNumber}"?`)) return;
    try {
      await axios.post(`${API}/admin/members/${serialNumber}/unsuspend`, {}, axiosConfig);
      toast.success('Member unsuspended successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to unsuspend member');
    }
  };

  // Pricelist CRUD
  const handlePricelistSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editMode.type === 'pricelist') {
        await axios.put(`${API}/admin/pricelists/${editMode.data.hospital_name}/${editMode.data.item_id}`, {
          item_name: pricelistForm.item_name,
          item_type: pricelistForm.item_type,
          cost: parseFloat(pricelistForm.cost)
        }, axiosConfig);
        toast.success('Price list item updated successfully');
      } else {
        await axios.post(`${API}/admin/pricelists`, {
          ...pricelistForm,
          cost: parseFloat(pricelistForm.cost)
        }, axiosConfig);
        toast.success('Price list item created successfully');
      }
      setPricelistDialog(false);
      setPricelistForm({ hospital_name: '', item_id: '', item_name: '', item_type: 'Service', cost: '' });
      setEditMode({ type: '', data: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePricelistDelete = async (hospitalName, itemId) => {
    if (!window.confirm(`Delete price list item "${itemId}"?`)) return;
    try {
      await axios.delete(`${API}/admin/pricelists/${hospitalName}/${itemId}`, axiosConfig);
      toast.success('Price list item deleted successfully');
      loadData();
    } catch (error) {
      toast.error('Failed to delete price list item');
    }
  };

  // Bill delete
  const handleClaimDelete = async (billId) => {
    if (!window.confirm(`Delete bill "${billId}"? This will refund the amount if the bill was completed.`)) return;
    try {
      await axios.delete(`${API}/admin/bills/${billId}`, axiosConfig);
      toast.success('Bill deleted successfully');
      loadData();
    } catch (error) {
      toast.error('Failed to delete bill');
    }
  };

  const openEditDialog = (type, data) => {
    setEditMode({ type, data });
    switch (type) {
      case 'hospital':
        setHospitalForm(data);
        setHospitalDialog(true);
        break;
      case 'user':
        setUserForm({ ...data, temporary_password: '', first_login: data.first_login });
        setUserDialog(true);
        break;
      case 'family':
        setFamilyForm(data);
        setFamilyDialog(true);
        break;
      case 'member':
        setMemberForm(data);
        setMemberDialog(true);
        break;
      case 'pricelist':
        setPricelistForm(data);
        setPricelistDialog(true);
        break;
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #e3f2fd 0%, #f0f4f8 100%)' }}>
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button onClick={() => navigate('/dashboard')} variant="outline" className="flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                {isSuperAdmin ? 'Admin Panel - CRUD Operations' : `${hospitalName} - Admin Panel`}
              </h1>
              <p className="text-sm text-gray-600">
                {isSuperAdmin ? 'Manage all system entities' : 'Manage hospital data'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <Tabs defaultValue={isSuperAdmin ? "hospitals" : "families"} className="space-y-6">
          <TabsList className={`grid w-full ${isSuperAdmin ? 'grid-cols-6' : 'grid-cols-4'} bg-white border border-gray-200 p-1 rounded-lg`}>
            {isSuperAdmin && (
              <>
                <TabsTrigger value="hospitals"><Building2 className="w-4 h-4 mr-2" />Hospitals</TabsTrigger>
                <TabsTrigger value="users"><UserPlus className="w-4 h-4 mr-2" />Users</TabsTrigger>
              </>
            )}
            <TabsTrigger value="families"><UsersRound className="w-4 h-4 mr-2" />Families</TabsTrigger>
            <TabsTrigger value="members"><Users className="w-4 h-4 mr-2" />Members</TabsTrigger>
            <TabsTrigger value="pricelists"><FileText className="w-4 h-4 mr-2" />Price Lists</TabsTrigger>
            <TabsTrigger value="bills"><Receipt className="w-4 h-4 mr-2" />Claims</TabsTrigger>
          </TabsList>

          {/* Hospitals Tab - Superadmin Only */}
          {isSuperAdmin && (
          <TabsContent value="hospitals">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Hospitals</CardTitle>
                <Dialog open={hospitalDialog} onOpenChange={setHospitalDialog}>
                  <DialogTrigger asChild>
                    <Button onClick={() => { setEditMode({ type: '', data: null }); setHospitalForm({ hospital_name: '', address: '', phone: '', email: '' }); }}>
                      <Plus className="w-4 h-4 mr-2" />Add Hospital
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editMode.type === 'hospital' ? 'Edit Hospital' : 'Add Hospital'}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleHospitalSubmit} className="space-y-4">
                      <div>
                        <Label>Hospital Name</Label>
                        <Input value={hospitalForm.hospital_name} onChange={(e) => setHospitalForm({...hospitalForm, hospital_name: e.target.value})} required disabled={editMode.type === 'hospital'} />
                      </div>
                      <div>
                        <Label>Address</Label>
                        <Input value={hospitalForm.address} onChange={(e) => setHospitalForm({...hospitalForm, address: e.target.value})} />
                      </div>
                      <div>
                        <Label>Phone</Label>
                        <Input value={hospitalForm.phone} onChange={(e) => setHospitalForm({...hospitalForm, phone: e.target.value})} />
                      </div>
                      <div>
                        <Label>Email</Label>
                        <Input type="email" value={hospitalForm.email} onChange={(e) => setHospitalForm({...hospitalForm, email: e.target.value})} />
                      </div>
                      <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Saving...' : editMode.type === 'hospital' ? 'Update' : 'Create'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Hospital Name</th>
                      <th className="text-left p-3 text-sm font-semibold">Address</th>
                      <th className="text-left p-3 text-sm font-semibold">Phone</th>
                      <th className="text-left p-3 text-sm font-semibold">Email</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {hospitals.map((hospital) => (
                      <tr key={hospital.hospital_name} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium">{hospital.hospital_name}</td>
                        <td className="p-3 text-sm">{hospital.address}</td>
                        <td className="p-3 text-sm">{hospital.phone}</td>
                        <td className="p-3 text-sm">{hospital.email}</td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => openEditDialog('hospital', hospital)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleHospitalDelete(hospital.hospital_name)} className="text-red-600">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
          )}

          {/* Users Tab - Superadmin Only */}
          {isSuperAdmin && (
          <TabsContent value="users">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Users</CardTitle>
                <Dialog open={userDialog} onOpenChange={setUserDialog}>
                  <DialogTrigger asChild>
                    <Button onClick={() => { setEditMode({ type: '', data: null }); setUserForm({ username: '', hospital_name: '', role: 'Billing Clerk', temporary_password: '', first_login: true }); }}>
                      <Plus className="w-4 h-4 mr-2" />Add User
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editMode.type === 'user' ? 'Edit User' : 'Add User'}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleUserSubmit} className="space-y-4">
                      <div>
                        <Label>Username</Label>
                        <Input value={userForm.username} onChange={(e) => setUserForm({...userForm, username: e.target.value})} required disabled={editMode.type === 'user'} />
                      </div>
                      <div>
                        <Label>Hospital</Label>
                        <Select value={userForm.hospital_name} onValueChange={(value) => setUserForm({...userForm, hospital_name: value})}>
                          <SelectTrigger><SelectValue placeholder="Select hospital" /></SelectTrigger>
                          <SelectContent>
                            {hospitals.map((h) => (
                              <SelectItem key={h.hospital_name} value={h.hospital_name}>{h.hospital_name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Role</Label>
                        <Select value={userForm.role} onValueChange={(value) => setUserForm({...userForm, role: value})}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {ROLES.map((r) => (<SelectItem key={r} value={r}>{r}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </div>
                      {editMode.type !== 'user' && (
                        <div>
                          <Label>Temporary Password</Label>
                          <Input type="password" value={userForm.temporary_password} onChange={(e) => setUserForm({...userForm, temporary_password: e.target.value})} required />
                        </div>
                      )}
                      <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Saving...' : editMode.type === 'user' ? 'Update' : 'Create'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Username</th>
                      <th className="text-left p-3 text-sm font-semibold">Hospital</th>
                      <th className="text-left p-3 text-sm font-semibold">Role</th>
                      <th className="text-center p-3 text-sm font-semibold">First Login</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.username} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium">{user.username}</td>
                        <td className="p-3 text-sm">{user.hospital_name}</td>
                        <td className="p-3 text-sm">{user.role}</td>
                        <td className="p-3 text-center text-sm">{user.first_login ? 'Yes' : 'No'}</td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => openEditDialog('user', user)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleUserDelete(user.username)} className="text-red-600" disabled={user.username === 'superadmin'}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
          )}

          {/* Families Tab */}
          <TabsContent value="families">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Families</CardTitle>
                <Dialog open={familyDialog} onOpenChange={setFamilyDialog}>
                  <DialogTrigger asChild>
                    <Button onClick={() => { setEditMode({ type: '', data: null }); setFamilyForm({ family_id: '', principle_member_name: '', total_allotment: '', remaining_balance: '' }); }}>
                      <Plus className="w-4 h-4 mr-2" />Add Family
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editMode.type === 'family' ? 'Edit Family' : 'Add Family'}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleFamilySubmit} className="space-y-4">
                      <div>
                        <Label>Family ID</Label>
                        <Input value={familyForm.family_id} onChange={(e) => setFamilyForm({...familyForm, family_id: e.target.value})} required disabled={editMode.type === 'family'} />
                      </div>
                      <div>
                        <Label>Principle Member Name</Label>
                        <Input value={familyForm.principle_member_name} onChange={(e) => setFamilyForm({...familyForm, principle_member_name: e.target.value})} required />
                      </div>
                      <div>
                        <Label>Total Allotment ($)</Label>
                        <Input type="number" step="0.01" value={familyForm.total_allotment} onChange={(e) => setFamilyForm({...familyForm, total_allotment: e.target.value})} required />
                      </div>
                      <div>
                        <Label>Remaining Balance ($)</Label>
                        <Input type="number" step="0.01" value={familyForm.remaining_balance} onChange={(e) => setFamilyForm({...familyForm, remaining_balance: e.target.value})} required />
                      </div>
                      <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Saving...' : editMode.type === 'family' ? 'Update' : 'Create'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Family ID</th>
                      <th className="text-left p-3 text-sm font-semibold">Principle Member</th>
                      <th className="text-right p-3 text-sm font-semibold">Total Allotment</th>
                      <th className="text-right p-3 text-sm font-semibold">Remaining Balance</th>
                      <th className="text-center p-3 text-sm font-semibold">Status</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {families.map((family) => (
                      <tr key={family.family_id} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium">{family.family_id}</td>
                        <td className="p-3 text-sm">{family.principle_member_name}</td>
                        <td className="p-3 text-sm text-right">${family.total_allotment.toFixed(2)}</td>
                        <td className="p-3 text-sm text-right font-medium">${family.remaining_balance.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                            family.status === 'Suspended' 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {family.status || 'Active'}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => openEditDialog('family', family)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            {(family.status === 'Suspended') ? (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => handleFamilyUnsuspend(family.family_id)} 
                                className="text-green-600"
                                title="Unsuspend Family"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </Button>
                            ) : (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => handleFamilySuspend(family.family_id)} 
                                className="text-orange-600"
                                title="Suspend Family"
                              >
                                <Ban className="w-4 h-4" />
                              </Button>
                            )}
                            <Button variant="ghost" size="sm" onClick={() => handleFamilyDelete(family.family_id)} className="text-red-600">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Members Tab */}
          <TabsContent value="members">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Members</CardTitle>
                <Dialog open={memberDialog} onOpenChange={setMemberDialog}>
                  <DialogTrigger asChild>
                    <Button onClick={() => { setEditMode({ type: '', data: null }); setMemberForm({ serial_number: '', family_id: '', first_name: '', middle_name: '', last_name: '', dob: '', sex: 'Male', relationship: 'Principle' }); }}>
                      <Plus className="w-4 h-4 mr-2" />Add Member
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editMode.type === 'member' ? 'Edit Member' : 'Add Member'}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleMemberSubmit} className="space-y-4">
                      <div>
                        <Label>Serial Number</Label>
                        <Input value={memberForm.serial_number} onChange={(e) => setMemberForm({...memberForm, serial_number: e.target.value})} required disabled={editMode.type === 'member'} />
                      </div>
                      <div>
                        <Label>Family ID</Label>
                        <Select value={memberForm.family_id} onValueChange={(value) => setMemberForm({...memberForm, family_id: value})} disabled={editMode.type === 'member'}>
                          <SelectTrigger><SelectValue placeholder="Select family" /></SelectTrigger>
                          <SelectContent>
                            {families.map((f) => (<SelectItem key={f.family_id} value={f.family_id}>{f.family_id} - {f.principle_member_name}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>First Name</Label>
                          <Input value={memberForm.first_name} onChange={(e) => setMemberForm({...memberForm, first_name: e.target.value})} required />
                        </div>
                        <div>
                          <Label>Last Name</Label>
                          <Input value={memberForm.last_name} onChange={(e) => setMemberForm({...memberForm, last_name: e.target.value})} required />
                        </div>
                      </div>
                      <div>
                        <Label>Middle Name</Label>
                        <Input value={memberForm.middle_name} onChange={(e) => setMemberForm({...memberForm, middle_name: e.target.value})} />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>Date of Birth</Label>
                          <Input type="date" value={memberForm.dob} onChange={(e) => setMemberForm({...memberForm, dob: e.target.value})} required />
                        </div>
                        <div>
                          <Label>Sex</Label>
                          <Select value={memberForm.sex} onValueChange={(value) => setMemberForm({...memberForm, sex: value})}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Male">Male</SelectItem>
                              <SelectItem value="Female">Female</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div>
                        <Label>Relationship</Label>
                        <Select value={memberForm.relationship} onValueChange={(value) => setMemberForm({...memberForm, relationship: value})}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {RELATIONSHIPS.map((r) => (<SelectItem key={r} value={r}>{r}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </div>
                      <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Saving...' : editMode.type === 'member' ? 'Update' : 'Create'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Serial Number</th>
                      <th className="text-left p-3 text-sm font-semibold">Name</th>
                      <th className="text-left p-3 text-sm font-semibold">Family ID</th>
                      <th className="text-left p-3 text-sm font-semibold">Relationship</th>
                      <th className="text-center p-3 text-sm font-semibold">Status</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {members.map((member) => (
                      <tr key={member.serial_number} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium">{member.serial_number}</td>
                        <td className="p-3 text-sm">{member.first_name} {member.middle_name} {member.last_name}</td>
                        <td className="p-3 text-sm">{member.family_id}</td>
                        <td className="p-3 text-sm">{member.relationship}</td>
                        <td className="p-3 text-center">
                          <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                            member.status === 'Suspended' 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {member.status || 'Active'}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => openEditDialog('member', member)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            {(member.status === 'Suspended') ? (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => handleMemberUnsuspend(member.serial_number)} 
                                className="text-green-600"
                                title="Unsuspend Member"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </Button>
                            ) : (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => handleMemberSuspend(member.serial_number)} 
                                className="text-orange-600"
                                title="Suspend Member"
                              >
                                <Ban className="w-4 h-4" />
                              </Button>
                            )}
                            <Button variant="ghost" size="sm" onClick={() => handleMemberDelete(member.serial_number)} className="text-red-600">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Price Lists Tab */}
          <TabsContent value="pricelists">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Price Lists</CardTitle>
                <Dialog open={pricelistDialog} onOpenChange={setPricelistDialog}>
                  <DialogTrigger asChild>
                    <Button onClick={() => { setEditMode({ type: '', data: null }); setPricelistForm({ hospital_name: '', item_id: '', item_name: '', item_type: 'Service', cost: '' }); }}>
                      <Plus className="w-4 h-4 mr-2" />Add Price Item
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editMode.type === 'pricelist' ? 'Edit Price Item' : 'Add Price Item'}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handlePricelistSubmit} className="space-y-4">
                      <div>
                        <Label>Hospital</Label>
                        <Select value={pricelistForm.hospital_name} onValueChange={(value) => setPricelistForm({...pricelistForm, hospital_name: value})} disabled={editMode.type === 'pricelist'}>
                          <SelectTrigger><SelectValue placeholder="Select hospital" /></SelectTrigger>
                          <SelectContent>
                            {hospitals.map((h) => (<SelectItem key={h.hospital_name} value={h.hospital_name}>{h.hospital_name}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Item ID</Label>
                        <Input value={pricelistForm.item_id} onChange={(e) => setPricelistForm({...pricelistForm, item_id: e.target.value})} required disabled={editMode.type === 'pricelist'} />
                      </div>
                      <div>
                        <Label>Item Name</Label>
                        <Input value={pricelistForm.item_name} onChange={(e) => setPricelistForm({...pricelistForm, item_name: e.target.value})} required />
                      </div>
                      <div>
                        <Label>Item Type</Label>
                        <Select value={pricelistForm.item_type} onValueChange={(value) => setPricelistForm({...pricelistForm, item_type: value})}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Service">Service</SelectItem>
                            <SelectItem value="Drug">Drug</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Cost ($)</Label>
                        <Input type="number" step="0.01" value={pricelistForm.cost} onChange={(e) => setPricelistForm({...pricelistForm, cost: e.target.value})} required />
                      </div>
                      <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Saving...' : editMode.type === 'pricelist' ? 'Update' : 'Create'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Hospital</th>
                      <th className="text-left p-3 text-sm font-semibold">Item ID</th>
                      <th className="text-left p-3 text-sm font-semibold">Item Name</th>
                      <th className="text-left p-3 text-sm font-semibold">Type</th>
                      <th className="text-right p-3 text-sm font-semibold">Cost</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pricelists.map((item, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-sm">{item.hospital_name}</td>
                        <td className="p-3 text-sm font-medium">{item.item_id}</td>
                        <td className="p-3 text-sm">{item.item_name}</td>
                        <td className="p-3 text-sm">{item.item_type}</td>
                        <td className="p-3 text-sm text-right font-medium">${item.cost.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => openEditDialog('pricelist', item)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handlePricelistDelete(item.hospital_name, item.item_id)} className="text-red-600">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Claims Tab */}
          <TabsContent value="bills">
            <Card>
              <CardHeader>
                <CardTitle>
                  {isSuperAdmin ? 'All Claims (View & Delete)' : `${hospitalName} Claims (View & Delete)`}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Bill ID</th>
                      <th className="text-left p-3 text-sm font-semibold">Hospital</th>
                      <th className="text-left p-3 text-sm font-semibold">Patient</th>
                      <th className="text-left p-3 text-sm font-semibold">Date</th>
                      <th className="text-right p-3 text-sm font-semibold">Amount</th>
                      <th className="text-center p-3 text-sm font-semibold">Status</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {claims.map((bill) => (
                      <tr key={bill.bill_id} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium">{bill.bill_id}</td>
                        <td className="p-3 text-sm">{bill.hospital_name}</td>
                        <td className="p-3 text-sm">{bill.patient_name}</td>
                        <td className="p-3 text-sm">{new Date(bill.timestamp).toLocaleDateString()}</td>
                        <td className="p-3 text-sm text-right font-medium">${bill.total_bill_amount.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${bill.status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {bill.status}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => window.open(`/print/${bill.bill_id}`, '_blank')}
                              className="text-blue-600 hover:bg-blue-50"
                              title="Print Bill"
                            >
                              <Printer className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => handleClaimDelete(bill.bill_id)} 
                              className="text-red-600 hover:bg-red-50"
                              title="Delete Bill"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminCRUD;
