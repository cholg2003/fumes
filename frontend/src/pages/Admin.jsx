import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { ArrowLeft, Users, DollarSign, FileText, Trash2, UserPlus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Admin = () => {
  const navigate = useNavigate();
  const [families, setFamilies] = useState([]);
  const [members, setMembers] = useState([]);
  const [pricelists, setPricelists] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(false);

  // Family form
  const [familyForm, setFamilyForm] = useState({
    family_id: '',
    principle_member_name: '',
    total_allotment: '',
    remaining_balance: ''
  });

  // Member form
  const [memberForm, setMemberForm] = useState({
    serial_number: '',
    family_id: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    dob: '',
    sex: '',
    relationship: ''
  });

  // Pricelist form
  const [pricelistForm, setPricelistForm] = useState({
    hospital_name: '',
    item_id: '',
    item_name: '',
    item_type: '',
    cost: ''
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
      setHospitals(hospitalsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleCreateFamily = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/families`, {
        ...familyForm,
        total_allotment: parseFloat(familyForm.total_allotment),
        remaining_balance: parseFloat(familyForm.remaining_balance)
      }, axiosConfig);
      toast.success('Family created successfully');
      setFamilyForm({
        family_id: '',
        principle_member_name: '',
        total_allotment: '',
        remaining_balance: ''
      });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create family');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMember = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/members`, memberForm, axiosConfig);
      toast.success('Member added successfully');
      setMemberForm({
        serial_number: '',
        family_id: '',
        first_name: '',
        middle_name: '',
        last_name: '',
        dob: '',
        sex: '',
        relationship: ''
      });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add member');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePricelistItem = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/pricelists`, {
        ...pricelistForm,
        cost: parseFloat(pricelistForm.cost)
      }, axiosConfig);
      toast.success('Price list item created successfully');
      setPricelistForm({
        hospital_name: '',
        item_id: '',
        item_name: '',
        item_type: '',
        cost: ''
      });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create item');
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
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <Tabs defaultValue="families" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-white border border-gray-200 p-1 rounded-lg">
            <TabsTrigger value="families" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Families & Members
            </TabsTrigger>
            <TabsTrigger value="pricelists" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Price Lists
            </TabsTrigger>
            <TabsTrigger value="view" className="flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              View All Data
            </TabsTrigger>
          </TabsList>

          {/* Families & Members Tab */}
          <TabsContent value="families" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Add Family */}
              <Card className="border-blue-200 shadow-md">
                <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200">
                  <CardTitle className="flex items-center gap-2 text-blue-900">
                    <Users className="w-5 h-5" />
                    Add New Family
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                  <form onSubmit={handleCreateFamily} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Family ID</Label>
                      <Input
                        data-testid="family-id-input"
                        placeholder="e.g., SEC-2417"
                        value={familyForm.family_id}
                        onChange={(e) => setFamilyForm({...familyForm, family_id: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Principle Member Name</Label>
                      <Input
                        placeholder="Full name"
                        value={familyForm.principle_member_name}
                        onChange={(e) => setFamilyForm({...familyForm, principle_member_name: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Total Allotment ($)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="5000.00"
                        value={familyForm.total_allotment}
                        onChange={(e) => setFamilyForm({...familyForm, total_allotment: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Remaining Balance ($)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="5000.00"
                        value={familyForm.remaining_balance}
                        onChange={(e) => setFamilyForm({...familyForm, remaining_balance: e.target.value})}
                        required
                      />
                    </div>
                    <Button
                      data-testid="create-family-button"
                      type="submit"
                      disabled={loading}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      Create Family
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Add Member */}
              <Card className="border-green-200 shadow-md">
                <CardHeader className="bg-gradient-to-r from-green-50 to-green-100 border-b border-green-200">
                  <CardTitle className="flex items-center gap-2 text-green-900">
                    <UserPlus className="w-5 h-5" />
                    Add Beneficiary/Member
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                  <form onSubmit={handleCreateMember} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Serial Number</Label>
                      <Input
                        data-testid="member-serial-input"
                        placeholder="e.g., SEC-2417-01"
                        value={memberForm.serial_number}
                        onChange={(e) => setMemberForm({...memberForm, serial_number: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Family ID</Label>
                      <Select
                        value={memberForm.family_id}
                        onValueChange={(value) => setMemberForm({...memberForm, family_id: value})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select family" />
                        </SelectTrigger>
                        <SelectContent>
                          {families.map((family) => (
                            <SelectItem key={family.family_id} value={family.family_id}>
                              {family.family_id} - {family.principle_member_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label>First Name</Label>
                        <Input
                          placeholder="First name"
                          value={memberForm.first_name}
                          onChange={(e) => setMemberForm({...memberForm, first_name: e.target.value})}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Middle Name</Label>
                        <Input
                          placeholder="Middle name"
                          value={memberForm.middle_name}
                          onChange={(e) => setMemberForm({...memberForm, middle_name: e.target.value})}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Last Name</Label>
                      <Input
                        placeholder="Last name"
                        value={memberForm.last_name}
                        onChange={(e) => setMemberForm({...memberForm, last_name: e.target.value})}
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label>Date of Birth</Label>
                        <Input
                          type="date"
                          value={memberForm.dob}
                          onChange={(e) => setMemberForm({...memberForm, dob: e.target.value})}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Sex</Label>
                        <Select
                          value={memberForm.sex}
                          onValueChange={(value) => setMemberForm({...memberForm, sex: value})}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Male">Male</SelectItem>
                            <SelectItem value="Female">Female</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Relationship</Label>
                      <Select
                        value={memberForm.relationship}
                        onValueChange={(value) => setMemberForm({...memberForm, relationship: value})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select relationship" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Principle">Principle</SelectItem>
                          <SelectItem value="Spouse">Spouse</SelectItem>
                          <SelectItem value="Child">Child</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button
                      data-testid="create-member-button"
                      type="submit"
                      disabled={loading}
                      className="w-full bg-green-600 hover:bg-green-700"
                    >
                      Add Member
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Price Lists Tab */}
          <TabsContent value="pricelists" className="space-y-6">
            <Card className="border-purple-200 shadow-md">
              <CardHeader className="bg-gradient-to-r from-purple-50 to-purple-100 border-b border-purple-200">
                <CardTitle className="flex items-center gap-2 text-purple-900">
                  <FileText className="w-5 h-5" />
                  Add Price List Item
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <form onSubmit={handleCreatePricelistItem} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Hospital Name</Label>
                      <Select
                        value={pricelistForm.hospital_name}
                        onValueChange={(value) => setPricelistForm({...pricelistForm, hospital_name: value})}
                      >
                        <SelectTrigger data-testid="pricelist-hospital-select">
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
                      <Label>Item ID</Label>
                      <Input
                        placeholder="e.g., SERV-006 or DRUG-005"
                        value={pricelistForm.item_id}
                        onChange={(e) => setPricelistForm({...pricelistForm, item_id: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Item Name</Label>
                      <Input
                        placeholder="e.g., CT Scan"
                        value={pricelistForm.item_name}
                        onChange={(e) => setPricelistForm({...pricelistForm, item_name: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Item Type</Label>
                      <Select
                        value={pricelistForm.item_type}
                        onValueChange={(value) => setPricelistForm({...pricelistForm, item_type: value})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Service">Service</SelectItem>
                          <SelectItem value="Drug">Drug</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Cost ($)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="100.00"
                        value={pricelistForm.cost}
                        onChange={(e) => setPricelistForm({...pricelistForm, cost: e.target.value})}
                        required
                      />
                    </div>
                  </div>
                  <Button
                    data-testid="create-pricelist-button"
                    type="submit"
                    disabled={loading}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    Add Price List Item
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
