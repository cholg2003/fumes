import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { ArrowLeft, Users, DollarSign, FileText, Trash2, UserPlus, Plus, Upload } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RELATIONSHIPS = ['Principle', 'Spouse', 'Father', 'Mother', 'Child', 'Dependent'];

const Admin = () => {
  const navigate = useNavigate();
  const [families, setFamilies] = useState([]);
  const [members, setMembers] = useState([]);
  const [pricelists, setPricelists] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(false);

  // Bulk family form (family + multiple members)
  const [bulkFamilyForm, setBulkFamilyForm] = useState({
    family_id: '',
    principle_member_name: '',
    total_allotment: '',
    remaining_balance: '',
    members: [
      { first_name: '', middle_name: '', last_name: '', dob: '', sex: 'Male', relationship: 'Principle' }
    ]
  });

  // Bulk pricelist
  const [bulkPricelistForm, setBulkPricelistForm] = useState({
    hospital_name: '',
    csvData: ''
  });

  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    if (role !== 'Admin') {
      toast.error('Access denied. Admin only.');
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
      const [familiesRes, membersRes, pricelistsRes, hospitalsRes] = await Promise.all([
        axios.get(`${API}/admin/families`, axiosConfig),
        axios.get(`${API}/admin/members`, axiosConfig),
        axios.get(`${API}/admin/pricelists/all`, axiosConfig),
        axios.get(`${API}/admin/hospitals`, axiosConfig)
      ]);
      setFamilies(familiesRes.data);
      setMembers(membersRes.data);
      setPricelists(pricelistsRes.data);
      // Extract hospital names from hospital objects
      setHospitals(hospitalsRes.data.map(h => h.hospital_name));
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleAddMember = () => {
    setBulkFamilyForm({
      ...bulkFamilyForm,
      members: [
        ...bulkFamilyForm.members,
        { first_name: '', middle_name: '', last_name: '', dob: '', sex: 'Male', relationship: 'Child' }
      ]
    });
  };

  const handleRemoveMember = (index) => {
    if (bulkFamilyForm.members.length === 1) {
      toast.error('Family must have at least one member');
      return;
    }
    const newMembers = bulkFamilyForm.members.filter((_, i) => i !== index);
    setBulkFamilyForm({ ...bulkFamilyForm, members: newMembers });
  };

  const handleMemberChange = (index, field, value) => {
    const newMembers = [...bulkFamilyForm.members];
    newMembers[index][field] = value;
    setBulkFamilyForm({ ...bulkFamilyForm, members: newMembers });
  };

  const handleCreateBulkFamily = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/admin/families/bulk`, {
        family_id: bulkFamilyForm.family_id,
        principle_member_name: bulkFamilyForm.principle_member_name,
        total_allotment: parseFloat(bulkFamilyForm.total_allotment),
        remaining_balance: parseFloat(bulkFamilyForm.remaining_balance),
        members: bulkFamilyForm.members
      }, axiosConfig);

      toast.success(response.data.message);
      setBulkFamilyForm({
        family_id: '',
        principle_member_name: '',
        total_allotment: '',
        remaining_balance: '',
        members: [
          { first_name: '', middle_name: '', last_name: '', dob: '', sex: 'Male', relationship: 'Principle' }
        ]
      });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create family');
    } finally {
      setLoading(false);
    }
  };

  const parseCsvPriceList = (csvText) => {
    const lines = csvText.trim().split('\n');
    const items = [];
    
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      const parts = line.split(',').map(p => p.trim());
      if (parts.length >= 4) {
        items.push({
          item_id: parts[0],
          item_name: parts[1],
          item_type: parts[2],
          cost: parts[3]
        });
      }
    }
    return items;
  };

  const handleBulkPricelistUpload = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const items = parseCsvPriceList(bulkPricelistForm.csvData);
      
      if (items.length === 0) {
        toast.error('No valid items found in CSV');
        return;
      }

      const response = await axios.post(`${API}/admin/pricelists/bulk`, {
        hospital_name: bulkPricelistForm.hospital_name,
        items
      }, axiosConfig);

      toast.success(response.data.message);
      setBulkPricelistForm({ hospital_name: '', csvData: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload price list');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePricelistItem = async (hospitalName, itemId) => {
    if (!window.confirm('Are you sure you want to delete this item?')) {
      return;
    }
    try {
      await axios.delete(`${API}/admin/pricelists/${hospitalName}/${itemId}`, axiosConfig);
      toast.success('Item deleted successfully');
      loadData();
    } catch (error) {
      toast.error('Failed to delete item');
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #e3f2fd 0%, #f0f4f8 100%)' }}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              data-testid="back-to-dashboard"
              onClick={() => navigate('/dashboard')}
              variant="outline"
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Admin Panel</h1>
              <p className="text-sm text-gray-600">System Management</p>
            </div>
          </div>
          <Button
            onClick={() => navigate('/admin/crud')}
            className="bg-purple-600 hover:bg-purple-700"
          >
            Manage All Data (CRUD)
          </Button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <Tabs defaultValue="families" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-white border border-gray-200 p-1 rounded-lg">
            <TabsTrigger value="families" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Add Family (Bulk)
            </TabsTrigger>
            <TabsTrigger value="pricelists" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Price Lists (Bulk)
            </TabsTrigger>
            <TabsTrigger value="view" className="flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              View All Data
            </TabsTrigger>
          </TabsList>

          {/* Bulk Family Creation Tab */}
          <TabsContent value="families">
            <Card className="border-blue-200 shadow-md">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200">
                <CardTitle className="flex items-center gap-2 text-blue-900">
                  <Users className="w-5 h-5" />
                  Add Family with Members
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <form onSubmit={handleCreateBulkFamily} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="space-y-2">
                      <Label>Family ID</Label>
                      <Input
                        data-testid="bulk-family-id-input"
                        placeholder="e.g., SEC-2425"
                        value={bulkFamilyForm.family_id}
                        onChange={(e) => setBulkFamilyForm({...bulkFamilyForm, family_id: e.target.value})}
                        required
                      />
                      <p className="text-xs text-gray-600">Members will be: {bulkFamilyForm.family_id}-00, {bulkFamilyForm.family_id}-01, etc.</p>
                    </div>
                    <div className="space-y-2">
                      <Label>Principle Member Name</Label>
                      <Input
                        placeholder="Full name"
                        value={bulkFamilyForm.principle_member_name}
                        onChange={(e) => setBulkFamilyForm({...bulkFamilyForm, principle_member_name: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Total Allotment ($)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="5000.00"
                        value={bulkFamilyForm.total_allotment}
                        onChange={(e) => setBulkFamilyForm({...bulkFamilyForm, total_allotment: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Remaining Balance ($)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="5000.00"
                        value={bulkFamilyForm.remaining_balance}
                        onChange={(e) => setBulkFamilyForm({...bulkFamilyForm, remaining_balance: e.target.value})}
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-800">Family Members</h3>
                      <Button
                        type="button"
                        onClick={handleAddMember}
                        variant="outline"
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        <Plus className="w-4 h-4" />
                        Add Member
                      </Button>
                    </div>

                    {bulkFamilyForm.members.map((member, index) => (
                      <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-semibold text-gray-700">
                            Member {index + 1} - Serial: {bulkFamilyForm.family_id}-{String(index).padStart(2, '0')}
                          </span>
                          {bulkFamilyForm.members.length > 1 && (
                            <Button
                              type="button"
                              onClick={() => handleRemoveMember(index)}
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="space-y-2">
                            <Label>First Name</Label>
                            <Input
                              placeholder="First name"
                              value={member.first_name}
                              onChange={(e) => handleMemberChange(index, 'first_name', e.target.value)}
                              required
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Middle Name</Label>
                            <Input
                              placeholder="Middle name"
                              value={member.middle_name}
                              onChange={(e) => handleMemberChange(index, 'middle_name', e.target.value)}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Last Name</Label>
                            <Input
                              placeholder="Last name"
                              value={member.last_name}
                              onChange={(e) => handleMemberChange(index, 'last_name', e.target.value)}
                              required
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Date of Birth</Label>
                            <Input
                              type="date"
                              value={member.dob}
                              onChange={(e) => handleMemberChange(index, 'dob', e.target.value)}
                              required
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Sex</Label>
                            <Select
                              value={member.sex}
                              onValueChange={(value) => handleMemberChange(index, 'sex', value)}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Male">Male</SelectItem>
                                <SelectItem value="Female">Female</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Relationship</Label>
                            <Select
                              value={member.relationship}
                              onValueChange={(value) => handleMemberChange(index, 'relationship', value)}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {RELATIONSHIPS.map(rel => (
                                  <SelectItem key={rel} value={rel}>{rel}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <Button
                    data-testid="create-bulk-family-button"
                    type="submit"
                    disabled={loading}
                    className="w-full bg-blue-600 hover:bg-blue-700 h-12 text-lg font-semibold"
                  >
                    {loading ? 'Creating...' : `Create Family with ${bulkFamilyForm.members.length} Member(s)`}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Bulk Price Lists Tab */}
          <TabsContent value="pricelists" className="space-y-6">
            <Card className="border-purple-200 shadow-md">
              <CardHeader className="bg-gradient-to-r from-purple-50 to-purple-100 border-b border-purple-200">
                <CardTitle className="flex items-center gap-2 text-purple-900">
                  <Upload className="w-5 h-5" />
                  Bulk Upload Price List (CSV)
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <form onSubmit={handleBulkPricelistUpload} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Hospital Name</Label>
                    <Select
                      value={bulkPricelistForm.hospital_name}
                      onValueChange={(value) => setBulkPricelistForm({...bulkPricelistForm, hospital_name: value})}
                    >
                      <SelectTrigger data-testid="bulk-pricelist-hospital-select">
                        <SelectValue placeholder="Select hospital" />
                      </SelectTrigger>
                      <SelectContent>
                        {hospitals.map((hospital) => (
                          <SelectItem key={hospital} value={hospital}>
                            {hospital}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>CSV Data</Label>
                    <Textarea
                      data-testid="bulk-pricelist-csv-input"
                      placeholder="Paste CSV data here&#10;Format: item_id, item_name, item_type, cost&#10;Example:&#10;SERV-020, MRI Scan, Service, 500&#10;DRUG-010, Aspirin 100mg, Drug, 5"
                      value={bulkPricelistForm.csvData}
                      onChange={(e) => setBulkPricelistForm({...bulkPricelistForm, csvData: e.target.value})}
                      rows={10}
                      className="font-mono text-sm"
                      required
                    />
                    <p className="text-xs text-gray-600">Format: item_id, item_name, item_type (Service/Drug), cost</p>
                  </div>

                  <Button
                    data-testid="bulk-upload-pricelist-button"
                    type="submit"
                    disabled={loading}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    {loading ? 'Uploading...' : 'Upload Price List'}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Price List Table */}
            <Card className="border-gray-200 shadow-md">
              <CardHeader className="bg-gray-50 border-b border-gray-200">
                <CardTitle>All Price List Items</CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="overflow-x-auto">
                  <table className="w-full" data-testid="pricelists-table">
                    <thead className="bg-gray-100 border-b border-gray-200">
                      <tr>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Hospital</th>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Item ID</th>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Item Name</th>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Type</th>
                        <th className="text-right p-3 text-sm font-semibold text-gray-700">Cost</th>
                        <th className="text-center p-3 text-sm font-semibold text-gray-700">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pricelists.map((item, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="p-3 text-sm text-gray-800">{item.hospital_name}</td>
                          <td className="p-3 text-sm text-gray-800">{item.item_id}</td>
                          <td className="p-3 text-sm text-gray-800">{item.item_name}</td>
                          <td className="p-3 text-sm text-gray-600">{item.item_type}</td>
                          <td className="p-3 text-sm text-gray-800 text-right font-medium">${item.cost.toFixed(2)}</td>
                          <td className="p-3 text-center">
                            <Button
                              data-testid={`delete-pricelist-${index}`}
                              onClick={() => handleDeletePricelistItem(item.hospital_name, item.item_id)}
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* View All Data Tab */}
          <TabsContent value="view" className="space-y-6">
            {/* Families Table */}
            <Card className="border-gray-200 shadow-md">
              <CardHeader className="bg-gray-50 border-b border-gray-200">
                <CardTitle>All Families</CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="overflow-x-auto">
                  <table className="w-full" data-testid="families-table">
                    <thead className="bg-gray-100 border-b border-gray-200">
                      <tr>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Family ID</th>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Principle Member</th>
                        <th className="text-right p-3 text-sm font-semibold text-gray-700">Total Allotment</th>
                        <th className="text-right p-3 text-sm font-semibold text-gray-700">Remaining Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {families.map((family) => (
                        <tr key={family.family_id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="p-3 text-sm font-medium text-gray-800">{family.family_id}</td>
                          <td className="p-3 text-sm text-gray-800">{family.principle_member_name}</td>
                          <td className="p-3 text-sm text-gray-800 text-right">${family.total_allotment.toFixed(2)}</td>
                          <td className="p-3 text-sm text-gray-800 text-right font-medium">${family.remaining_balance.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Members Table */}
            <Card className="border-gray-200 shadow-md">
              <CardHeader className="bg-gray-50 border-b border-gray-200">
                <CardTitle>All Members</CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="overflow-x-auto">
                  <table className="w-full" data-testid="members-table">
                    <thead className="bg-gray-100 border-b border-gray-200">
                      <tr>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Serial Number</th>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Name</th>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Family ID</th>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">DOB</th>
                        <th className="text-left p-3 text-sm font-semibold text-gray-700">Relationship</th>
                      </tr>
                    </thead>
                    <tbody>
                      {members.map((member) => (
                        <tr key={member.serial_number} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="p-3 text-sm font-medium text-gray-800">{member.serial_number}</td>
                          <td className="p-3 text-sm text-gray-800">{member.first_name} {member.middle_name} {member.last_name}</td>
                          <td className="p-3 text-sm text-gray-600">{member.family_id}</td>
                          <td className="p-3 text-sm text-gray-600">{member.dob}</td>
                          <td className="p-3 text-sm text-gray-600">{member.relationship}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Admin;
