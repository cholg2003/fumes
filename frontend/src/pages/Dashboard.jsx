import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { LogOut, Search, User, DollarSign, Plus, Trash2, FileText, Ban, Printer, Settings, CheckCircle } from 'lucide-react';
import Pagination from '../components/Pagination';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [familyMembers, setFamilyMembers] = useState([]);
  const [familyInfo, setFamilyInfo] = useState(null);
  const [searchType, setSearchType] = useState(''); // 'individual' or 'family'
  const [priceList, setPriceList] = useState([]);
  const [claimItems, setClaimItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState('');
  const [itemQuantity, setItemQuantity] = useState(1);
  const [itemSearchQuery, setItemSearchQuery] = useState('');
  const [filteredPriceList, setFilteredPriceList] = useState([]);
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hospitalStats, setHospitalStats] = useState({});
  const [hospitalBalance, setHospitalBalance] = useState(0);
  const [totalClaims, setTotalClaims] = useState(0);
  
  // Pagination and filtering
  const [claimPage, setClaimPage] = useState(1);
  const [claimStatusFilter, setClaimStatusFilter] = useState('ALL');
  const ITEMS_PER_PAGE = 20;

  const token = localStorage.getItem('token');
  const hospitalName = localStorage.getItem('hospital_name');
  const username = localStorage.getItem('username');
  const role = localStorage.getItem('role');
  
  const isSuperAdmin = username === 'superadmin';

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    loadPriceList();
    loadClaims();
    loadHospitalBalance();
    loadHospitalStats();
  }, []);

  const axiosConfig = {
    headers: { Authorization: `Bearer ${token}` }
  };

  const loadPriceList = async () => {
    try {
      const response = await axios.get(`${API}/pricelists`, axiosConfig);
      setPriceList(response.data);
      setFilteredPriceList(response.data); // Initialize filtered list
      console.log('Price list loaded:', response.data.length, 'items');
    } catch (error) {
      toast.error('Failed to load price list');
      console.error('Price list error:', error);
    }
  };

  // Filter price list based on search query
  useEffect(() => {
    if (!itemSearchQuery.trim()) {
      setFilteredPriceList(priceList);
    } else {
      const query = itemSearchQuery.toLowerCase();
      const filtered = priceList.filter(item =>
        item.item_id.toLowerCase().includes(query) ||
        item.item_name.toLowerCase().includes(query)
      );
      setFilteredPriceList(filtered);
    }
  }, [itemSearchQuery, priceList]);

  const loadClaims = async () => {
    try {
      // Superadmin gets all claims, others get hospital-specific claims
      const endpoint = isSuperAdmin ? `${API}/admin/claims/all` : `${API}/claims`;
      const response = await axios.get(endpoint, axiosConfig);
      setClaims(response.data);
    } catch (error) {
      toast.error('Failed to load claims');
    }
  };

  const loadHospitalStats = async () => {
    try {
      const response = await axios.get(`${API}/claims/hospital-stats`, axiosConfig);
      setHospitalStats(response.data);
      
      // For non-superadmin, calculate total claims for their hospital
      if (!isSuperAdmin && hospitalName && response.data[hospitalName]) {
        setTotalClaims(response.data[hospitalName].total_pending);
      }
    } catch (error) {
      console.error('Failed to load hospital stats:', error);
    }
  };

  const loadHospitalBalance = async () => {
    try {
      const response = await axios.get(`${API}/hospital/balance`, axiosConfig);
      setHospitalBalance(response.data.deposit_balance);
    } catch (error) {
      console.error('Failed to load hospital balance:', error);
    }
  };


  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Please enter a search term');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`${API}/patients/search?query=${searchQuery}`, axiosConfig);
      const data = response.data;
      
      if (data.type === 'family') {
        // Family search result
        if (!data.family) {
          toast.error('No family found');
          setSelectedPatient(null);
          setFamilyMembers([]);
          setFamilyInfo(null);
          setSearchType('');
        } else {
          setFamilyInfo(data.family);
          setFamilyMembers(data.members);
          setSelectedPatient(null); // Clear individual selection
          setSearchType('family');
          toast.success(`Found family ${data.family.family_id} with ${data.members.length} members`);
        }
      } else {
        // Individual search result
        if (data.results.length === 0) {
          toast.error('No patients found');
          setSelectedPatient(null);
          setFamilyMembers([]);
          setFamilyInfo(null);
          setSearchType('');
        } else if (data.results.length === 1) {
          setSelectedPatient(data.results[0]);
          setFamilyMembers([]);
          setFamilyInfo(null);
          setSearchType('individual');
          toast.success('Patient found');
        } else {
          setSelectedPatient(data.results[0]);
          setFamilyMembers([]);
          setFamilyInfo(null);
          setSearchType('individual');
          toast.info(`Found ${data.results.length} patients, showing first result`);
        }
      }
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    if (!selectedItem) {
      toast.error('Please select an item');
      return;
    }

    if (itemQuantity < 1) {
      toast.error('Quantity must be at least 1');
      return;
    }

    console.log('Selected item ID:', selectedItem);
    console.log('Price list:', priceList);
    
    const item = priceList.find(p => p.item_id === selectedItem);
    console.log('Found item:', item);
    
    if (item) {
      setClaimItems([...claimItems, { ...item, quantity: itemQuantity }]);
      setSelectedItem('');
      setItemQuantity(1); // Reset quantity to 1
      toast.success(`Added ${itemQuantity}x ${item.item_name} to claim`);
    } else {
      toast.error('Item not found in price list');
    }
  };

  const handleRemoveItem = (index) => {
    const newItems = claimItems.filter((_, i) => i !== index);
    setClaimItems(newItems);
    toast.info('Item removed');
  };

  const getTotalClaimCost = () => {
    return claimItems.reduce((sum, item) => sum + (item.cost * (item.quantity || 1)), 0);
  };

  const handleSubmitClaim = async () => {
    if (!selectedPatient) {
      toast.error('Please select a patient');
      return;
    }

    if (claimItems.length === 0) {
      toast.error('Please add items to the claim');
      return;
    }

    const totalCost = getTotalClaimCost();
    if (totalCost > selectedPatient.remaining_balance) {
      toast.error(`Insufficient funds! Available: $${selectedPatient.remaining_balance.toFixed(2)}, Required: $${totalCost.toFixed(2)}`);
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/claims/submit`,
        {
          patient_serial_number: selectedPatient.serial_number,
          claim_items: claimItems.map(item => ({
            item_id: item.item_id,
            item_name: item.item_name,
            item_cost: item.cost,
            quantity: item.quantity || 1
          }))
        },
        axiosConfig
      );

      toast.success(`Claim created successfully! Claim ID: ${response.data.claim_id}`);
      setClaimItems([]);
      setSelectedPatient({
        ...selectedPatient,
        remaining_balance: response.data.new_balance
      });
      await loadClaims();
      await loadHospitalStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit bill');
    } finally {
      setLoading(false);
    }
  };

  const handleVoidClaim = async (claimId) => {
    if (!window.confirm('Are you sure you want to void this claim?')) {
      return;
    }

    try {
      await axios.post(`${API}/claims/${claimId}/void`, {}, axiosConfig);
      toast.success('Claim voided successfully');
      await loadClaims();
      await loadHospitalStats();
      if (selectedPatient) {
        const response = await axios.get(`${API}/patients/${selectedPatient.serial_number}`, axiosConfig);
        setSelectedPatient(response.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to void claim');
    }
  };

  // Pagination and filtering helpers
  const paginate = (array, page) => {
    const startIndex = (page - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    return array.slice(startIndex, endIndex);
  };

  const getTotalPages = (arrayLength) => {
    return Math.ceil(arrayLength / ITEMS_PER_PAGE);
  };

  // Filter claims by status
  const filteredClaims = claimStatusFilter === 'ALL' 
    ? claims 
    : claims.filter(claim => claim.status === claimStatusFilter);

  const paginatedClaims = paginate(filteredClaims, claimPage);

  // Reset to page 1 when filter changes
  useEffect(() => {
    setClaimPage(1);
  }, [claimStatusFilter]);

  const handleMarkAsPaid = async (claimId, claimAmount) => {
    if (!window.confirm(`Mark this claim as paid? This will deduct $${claimAmount.toFixed(2)} from your hospital balance.`)) {
      return;
    }

    try {
      const response = await axios.post(`${API}/claims/${claimId}/pay`, {}, axiosConfig);
      toast.success(response.data.message);
      await loadClaims();
      await loadHospitalBalance(); // Refresh the balance
      await loadHospitalStats(); // Refresh the stats
      if (selectedPatient) {
        const patientResponse = await axios.get(`${API}/patients/${selectedPatient.serial_number}`, axiosConfig);
        setSelectedPatient(patientResponse.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to mark claim as paid');
    }
  };


  const handlePrintClaim = (claimId) => {
    window.open(`/print/${claimId}`, '_blank');
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
    toast.info('Logged out');
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #e3f2fd 0%, #f0f4f8 100%)' }}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {role === 'Reception' ? 'Patient Search' : role === 'Finance' ? 'Claims Dashboard' : 'Hospital Dashboard'}
            </h1>
            <p className="text-sm text-gray-600 mt-1">{hospitalName} • {username} • {role}</p>
          </div>
          <div className="flex items-center gap-3">
            {isSuperAdmin && (
              <Button
                data-testid="admin-panel-button"
                onClick={() => navigate('/admin')}
                variant="outline"
                className="flex items-center gap-2 border-purple-300 text-purple-700 hover:bg-purple-50"
              >
                <Settings className="w-4 h-4" />
                Admin Panel
              </Button>
            )}
            <Button
              data-testid="logout-button"
              onClick={handleLogout}
              variant="outline"
              className="flex items-center gap-2 border-gray-300 hover:bg-gray-50"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-6">

        {/* Hospital Financial Status - For Admin and Finance */}
        {(role === 'Admin' || role === 'Finance') && !isSuperAdmin && (
          <Card className={`shadow-md ${totalClaims > hospitalBalance ? 'border-green-300' : 'border-red-300'}`}>
            <CardHeader className={`bg-gradient-to-r ${totalClaims > hospitalBalance ? 'from-green-50 to-green-100 border-green-200' : 'from-red-50 to-red-100 border-red-200'} border-b`}>
              <CardTitle className={`${totalClaims > hospitalBalance ? 'text-green-900' : 'text-red-900'}`}>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5" />
                    Financial Status
                  </span>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Total Claims</p>
                  <p className="text-2xl font-bold text-blue-600">${totalClaims.toFixed(2)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Deposit Balance</p>
                  <p className="text-2xl font-bold text-purple-600">${hospitalBalance.toFixed(2)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Net Balance</p>
                  <p className={`text-3xl font-bold ${totalClaims > hospitalBalance ? 'text-green-600' : 'text-red-600'}`}>
                    {totalClaims > hospitalBalance ? '+' : ''}${(totalClaims - hospitalBalance).toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {totalClaims > hospitalBalance 
                      ? 'Insurance owes hospital' 
                      : totalClaims < hospitalBalance
                      ? 'Hospital owes insurance'
                      : 'Balanced'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Hospital Claims Overview - Superadmin Only */}
        {isSuperAdmin && Object.keys(hospitalStats).length > 0 && (
          <Card className="border-red-200 shadow-md">
            <CardHeader className="bg-gradient-to-r from-red-50 to-red-100 border-b border-red-200">
              <CardTitle className="flex items-center gap-2 text-red-900">
                <DollarSign className="w-5 h-5" />
                Outstanding Claims by Hospital
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(hospitalStats).map(([hospital, stats]) => (
                  <div key={hospital} className="bg-gradient-to-br from-red-50 to-white p-6 rounded-xl border border-red-200 shadow-sm">
                    <h3 className="font-semibold text-gray-800 mb-3">{hospital}</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Pending Claims:</span>
                        <span className="text-sm font-medium text-blue-600">{stats.pending_count} (${stats.total_pending.toFixed(2)})</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Paid Claims:</span>
                        <span className="text-sm font-medium text-green-600">{stats.paid_count} (${stats.total_paid.toFixed(2)})</span>
                      </div>
                      <div className="border-t pt-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-semibold text-gray-700">Outstanding:</span>
                          <span className="text-2xl font-bold text-red-600">-${stats.outstanding.toFixed(2)}</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1 text-right">Insurance owes hospital</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Patient Search */}
        <Card className="border-blue-200 shadow-md">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200">
            <CardTitle className="flex items-center gap-2 text-blue-900">
              <Search className="w-5 h-5" />
              Patient Search
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="flex gap-3">
              <div className="flex-1">
                <Input
                  data-testid="patient-search-input"
                  placeholder="Search by Serial Number or Name"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="h-11 border-gray-300"
                />
              </div>
              <Button
                data-testid="patient-search-button"
                onClick={handleSearch}
                disabled={loading}
                className="h-11 bg-blue-600 hover:bg-blue-700 px-8"
              >
                <Search className="w-4 h-4 mr-2" />
                Search
              </Button>
            </div>

            {selectedPatient && searchType === 'individual' && (
              <div className="mt-6 p-6 bg-gradient-to-br from-blue-50 to-white rounded-xl border border-blue-200" data-testid="patient-details">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-gray-700">
                      <User className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold">Patient:</span>
                      <span data-testid="patient-name">{selectedPatient.first_name} {selectedPatient.middle_name} {selectedPatient.last_name}</span>
                    </div>
                    <div className="text-sm text-gray-600">
                      <span className="font-medium">Serial:</span> <span data-testid="patient-serial">{selectedPatient.serial_number}</span>
                    </div>
                    <div className="text-sm text-gray-600">
                      <span className="font-medium">Family ID:</span> {selectedPatient.family_id}
                    </div>
                    <div className="text-sm text-gray-600">
                      <span className="font-medium">DOB:</span> {selectedPatient.dob} • {selectedPatient.sex}
                    </div>
                  </div>
                  <div className="flex items-center justify-center md:justify-end">
                    <div className="bg-gradient-to-br from-green-500 to-green-600 text-white px-8 py-6 rounded-2xl shadow-lg text-center">
                      <DollarSign className="w-8 h-8 mx-auto mb-2" />
                      <div className="text-sm font-medium opacity-90">Available Balance</div>
                      <div className="text-3xl font-bold" data-testid="patient-balance">${selectedPatient.remaining_balance.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {familyInfo && searchType === 'family' && (
              <div className="mt-6 space-y-4">
                {/* Family Balance Card */}
                <div className="p-6 bg-gradient-to-br from-green-50 to-white rounded-xl border border-green-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-gray-800 mb-1">Family: {familyInfo.family_id}</h3>
                      <p className="text-sm text-gray-600">Principle: {familyInfo.principle_member_name}</p>
                    </div>
                    <div className="bg-gradient-to-br from-green-500 to-green-600 text-white px-8 py-6 rounded-2xl shadow-lg text-center">
                      <DollarSign className="w-8 h-8 mx-auto mb-2" />
                      <div className="text-sm font-medium opacity-90">Family Balance</div>
                      <div className="text-3xl font-bold">${familyInfo.remaining_balance.toFixed(2)}</div>
                    </div>
                  </div>
                </div>

                {/* Family Members Table */}
                <div className="bg-white rounded-xl border border-blue-200 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-6 py-4 border-b border-blue-200">
                    <h3 className="font-bold text-blue-900">Family Members ({familyMembers.length})</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">Serial Number</th>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">Name</th>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">DOB</th>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">Sex</th>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">Relationship</th>
                          {(role === 'Finance' || role === 'Admin' || isSuperAdmin) && (
                            <th className="text-center p-3 text-sm font-semibold text-gray-700">Action</th>
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {familyMembers.map((member) => (
                          <tr key={member.serial_number} className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="p-3 text-sm font-medium text-gray-800">{member.serial_number}</td>
                            <td className="p-3 text-sm text-gray-800">{member.first_name} {member.middle_name} {member.last_name}</td>
                            <td className="p-3 text-sm text-gray-600">{member.dob}</td>
                            <td className="p-3 text-sm text-gray-600">{member.sex}</td>
                            <td className="p-3 text-sm text-gray-600">{member.relationship}</td>
                            {(role === 'Finance' || role === 'Admin' || isSuperAdmin) && (
                              <td className="p-3 text-center">
                                <Button
                                  onClick={() => {
                                    setSelectedPatient({
                                      ...member,
                                      remaining_balance: familyInfo.remaining_balance
                                    });
                                    setSearchType('individual');
                                  }}
                                  size="sm"
                                  className="bg-blue-600 hover:bg-blue-700"
                                >
                                  Create Bill
                                </Button>
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Claim Creation */}
        {selectedPatient && (role === 'Finance' || role === 'Admin') && (
          <Card className="border-green-200 shadow-md">
            <CardHeader className="bg-gradient-to-r from-green-50 to-green-100 border-b border-green-200">
              <CardTitle className="flex items-center gap-2 text-green-900">
                <FileText className="w-5 h-5" />
                Create New Claim
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div className="space-y-3">
                <div>
                  <Label className="text-gray-700 font-medium mb-2 block">Search Items</Label>
                  <Input
                    data-testid="item-search-input"
                    placeholder="Search by Item ID or Item Name"
                    value={itemSearchQuery}
                    onChange={(e) => setItemSearchQuery(e.target.value)}
                    className="h-11 border-gray-300"
                  />
                  {filteredPriceList.length === 0 && itemSearchQuery && (
                    <p className="text-sm text-gray-500 mt-1">No items found matching "{itemSearchQuery}"</p>
                  )}
                  {filteredPriceList.length > 0 && itemSearchQuery && (
                    <p className="text-sm text-gray-600 mt-1">Found {filteredPriceList.length} item(s)</p>
                  )}
                </div>
                <div className="flex gap-3">
                  <div className="flex-1">
                    <Label className="text-gray-700 font-medium mb-2 block">Select Service/Drug</Label>
                    <Select value={selectedItem} onValueChange={setSelectedItem}>
                      <SelectTrigger data-testid="item-select" className="h-11 border-gray-300">
                        <SelectValue placeholder="Choose an item" />
                      </SelectTrigger>
                      <SelectContent>
                        {filteredPriceList.map((item) => (
                          <SelectItem key={item.item_id} value={item.item_id}>
                            {item.item_id} - {item.item_name} - ${item.cost.toFixed(2)} ({item.item_type})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-700 font-medium mb-2 block">Quantity</Label>
                    <Input
                      type="number"
                      min="1"
                      value={itemQuantity}
                      onChange={(e) => setItemQuantity(parseInt(e.target.value) || 1)}
                      className="h-11 w-24 border-gray-300"
                      data-testid="item-quantity-input"
                    />
                  </div>
                  <div className="pt-7">
                    <Button
                      data-testid="add-item-button"
                      onClick={handleAddItem}
                      className="h-11 bg-green-600 hover:bg-green-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Item
                    </Button>
                  </div>
                </div>
              </div>

              {claimItems.length > 0 && (
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
                    <table className="w-full" data-testid="claim-items-table">
                      <thead className="bg-gray-100 border-b border-gray-200">
                        <tr>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">Item</th>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">Type</th>
                          <th className="text-right p-3 text-sm font-semibold text-gray-700">Unit Cost</th>
                          <th className="text-center p-3 text-sm font-semibold text-gray-700">Quantity</th>
                          <th className="text-right p-3 text-sm font-semibold text-gray-700">Total</th>
                          <th className="text-center p-3 text-sm font-semibold text-gray-700">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {claimItems.map((item, index) => (
                          <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="p-3 text-sm text-gray-800">{item.item_name}</td>
                            <td className="p-3 text-sm text-gray-600">{item.item_type}</td>
                            <td className="p-3 text-sm text-gray-600 text-right">${item.cost.toFixed(2)}</td>
                            <td className="p-3 text-sm text-gray-800 text-center font-medium">{item.quantity || 1}</td>
                            <td className="p-3 text-sm text-gray-800 text-right font-bold">${(item.cost * (item.quantity || 1)).toFixed(2)}</td>
                            <td className="p-3 text-center">
                              <Button
                                data-testid={`remove-item-${index}`}
                                onClick={() => handleRemoveItem(index)}
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

                  <div className="flex items-center justify-between p-6 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-200">
                    <div className="text-xl font-bold text-gray-800">
                      Total: <span data-testid="total-claim-cost" className="text-blue-600">${getTotalClaimCost().toFixed(2)}</span>
                    </div>
                    <Button
                      data-testid="submit-claim-button"
                      onClick={handleSubmitClaim}
                      disabled={loading}
                      className="h-12 px-8 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold shadow-md"
                    >
                      Submit Claim
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Claim History */}
        {(role === 'Finance' || role === 'Admin') && (
          <Card className="border-purple-200 shadow-md">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-purple-100 border-b border-purple-200">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-purple-900">
                <FileText className="w-5 h-5" />
                Recent Claims
              </CardTitle>
              <div className="flex items-center gap-2">
                <Label className="text-sm text-purple-800">Filter by Status:</Label>
                <Select value={claimStatusFilter} onValueChange={setClaimStatusFilter}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Status</SelectItem>
                    <SelectItem value="PENDING">Pending</SelectItem>
                    <SelectItem value="PAID">Paid</SelectItem>
                    <SelectItem value="VOIDED">Voided</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {claims.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No claims created yet</p>
            ) : (
              <>
                {claimStatusFilter !== 'ALL' && (
                  <div className="mb-4 text-sm text-gray-600">
                    Showing <strong>{filteredClaims.length}</strong> of <strong>{claims.length}</strong> claims
                  </div>
                )}
                <div className="overflow-x-auto">
                <table className="w-full" data-testid="claims-table">
                  <thead className="bg-gray-100 border-b border-gray-200">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold text-gray-700">Claim ID</th>
                      <th className="text-left p-3 text-sm font-semibold text-gray-700">Patient</th>
                      <th className="text-left p-3 text-sm font-semibold text-gray-700">Date</th>
                      <th className="text-right p-3 text-sm font-semibold text-gray-700">Amount</th>
                      <th className="text-center p-3 text-sm font-semibold text-gray-700">Status</th>
                      <th className="text-center p-3 text-sm font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedClaims.map((claim) => (
                      <tr key={claim.claim_id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium text-gray-800">{claim.claim_id}</td>
                        <td className="p-3 text-sm text-gray-700">{claim.patient_name}</td>
                        <td className="p-3 text-sm text-gray-600">{new Date(claim.timestamp).toLocaleDateString()}</td>
                        <td className="p-3 text-sm text-gray-800 text-right font-medium">${claim.total_claim_amount.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                            claim.status === 'PENDING' 
                              ? 'bg-yellow-100 text-yellow-800' 
                              : claim.status === 'PAID'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {claim.status}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button
                              data-testid={`print-claim-${claim.claim_id}`}
                              onClick={() => handlePrintClaim(claim.claim_id)}
                              variant="ghost"
                              size="sm"
                              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                            >
                              <Printer className="w-4 h-4" />
                            </Button>
                            {claim.status === 'PENDING' && isSuperAdmin && (
                              <>
                                <Button
                                  data-testid={`pay-claim-${claim.claim_id}`}
                                  onClick={() => handleMarkAsPaid(claim.claim_id, claim.total_claim_amount)}
                                  variant="ghost"
                                  size="sm"
                                  className="text-green-600 hover:text-green-700 hover:bg-green-50"
                                  title="Mark as Paid"
                                >
                                  <CheckCircle className="w-4 h-4" />
                                </Button>
                                <Button
                                  data-testid={`void-claim-${claim.claim_id}`}
                                  onClick={() => handleVoidClaim(claim.claim_id)}
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  <Ban className="w-4 h-4" />
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
                {filteredClaims.length > ITEMS_PER_PAGE && (
                  <Pagination
                    currentPage={claimPage}
                    totalPages={getTotalPages(filteredClaims.length)}
                    onPageChange={setClaimPage}
                  />
                )}
                {claims.length > 0 && filteredClaims.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>No claims found with status: {claimStatusFilter}</p>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
        )}
      </div>
    </div>
  );
};

export default Dashboard;