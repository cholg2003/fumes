import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { LogOut, Search, User, DollarSign, Plus, Trash2, FileText, Ban, Printer, Settings } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [priceList, setPriceList] = useState([]);
  const [billItems, setBillItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState('');
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [monthlyStats, setMonthlyStats] = useState({});

  const token = localStorage.getItem('token');
  const hospitalName = localStorage.getItem('hospital_name');
  const username = localStorage.getItem('username');
  const role = localStorage.getItem('role');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    loadPriceList();
    loadBills();
    if (role === 'Admin') {
      loadMonthlyStats();
    }
  }, []);

  const axiosConfig = {
    headers: { Authorization: `Bearer ${token}` }
  };

  const loadPriceList = async () => {
    try {
      const response = await axios.get(`${API}/pricelists`, axiosConfig);
      setPriceList(response.data);
      console.log('Price list loaded:', response.data.length, 'items');
    } catch (error) {
      toast.error('Failed to load price list');
      console.error('Price list error:', error);
    }
  };

  const loadBills = async () => {
    try {
      const response = await axios.get(`${API}/bills`, axiosConfig);
      setBills(response.data);
    } catch (error) {
      toast.error('Failed to load bills');
    }
  };

  const loadMonthlyStats = async () => {
    try {
      const response = await axios.get(`${API}/bills/monthly-stats`, axiosConfig);
      setMonthlyStats(response.data);
    } catch (error) {
      console.error('Failed to load monthly stats:', error);
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
      if (response.data.length === 0) {
        toast.error('No patients found');
        setSelectedPatient(null);
      } else if (response.data.length === 1) {
        setSelectedPatient(response.data[0]);
        toast.success('Patient found');
      } else {
        setSelectedPatient(response.data[0]);
        toast.info(`Found ${response.data.length} patients, showing first result`);
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

    console.log('Selected item ID:', selectedItem);
    console.log('Price list:', priceList);
    
    const item = priceList.find(p => p.item_id === selectedItem);
    console.log('Found item:', item);
    
    if (item) {
      setBillItems([...billItems, item]);
      setSelectedItem('');
      toast.success('Item added to bill');
    } else {
      toast.error('Item not found in price list');
    }
  };

  const handleRemoveItem = (index) => {
    const newItems = billItems.filter((_, i) => i !== index);
    setBillItems(newItems);
    toast.info('Item removed');
  };

  const getTotalBillCost = () => {
    return billItems.reduce((sum, item) => sum + item.cost, 0);
  };

  const handleSubmitBill = async () => {
    if (!selectedPatient) {
      toast.error('Please select a patient');
      return;
    }

    if (billItems.length === 0) {
      toast.error('Please add items to the bill');
      return;
    }

    const totalCost = getTotalBillCost();
    if (totalCost > selectedPatient.remaining_balance) {
      toast.error(`Insufficient funds! Available: $${selectedPatient.remaining_balance.toFixed(2)}, Required: $${totalCost.toFixed(2)}`);
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/bills/submit`,
        {
          patient_serial_number: selectedPatient.serial_number,
          bill_items: billItems.map(item => ({
            item_id: item.item_id,
            item_name: item.item_name,
            item_cost: item.cost
          }))
        },
        axiosConfig
      );

      toast.success(`Bill created successfully! Bill ID: ${response.data.bill_id}`);
      setBillItems([]);
      setSelectedPatient({
        ...selectedPatient,
        remaining_balance: response.data.new_balance
      });
      await loadBills(); // Reload bills to update monthly stats
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit bill');
    } finally {
      setLoading(false);
    }
  };

  const handleVoidBill = async (billId) => {
    if (!window.confirm('Are you sure you want to void this bill?')) {
      return;
    }

    try {
      await axios.post(`${API}/bills/${billId}/void`, {}, axiosConfig);
      toast.success('Bill voided successfully');
      await loadBills();
      if (selectedPatient) {
        const response = await axios.get(`${API}/patients/${selectedPatient.serial_number}`, axiosConfig);
        setSelectedPatient(response.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to void bill');
    }
  };

  const handlePrintBill = (billId) => {
    window.open(`/print/${billId}`, '_blank');
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
            <h1 className="text-2xl font-bold text-gray-800">Medical Insurance Billing</h1>
            <p className="text-sm text-gray-600 mt-1">{hospitalName} • {username} • {role}</p>
          </div>
          <div className="flex items-center gap-3">
            {role === 'Admin' && (
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
        {/* Monthly Billing Summary */}
        {role === 'Admin' && Object.keys(monthlyStats).length > 0 && (
          <Card className="border-indigo-200 shadow-md">
            <CardHeader className="bg-gradient-to-r from-indigo-50 to-indigo-100 border-b border-indigo-200">
              <CardTitle className="flex items-center gap-2 text-indigo-900">
                <DollarSign className="w-5 h-5" />
                Monthly Billing Summary - {new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(monthlyStats).map(([hospital, stats]) => (
                  <div key={hospital} className="bg-gradient-to-br from-indigo-50 to-white p-6 rounded-xl border border-indigo-200 shadow-sm">
                    <h3 className="font-semibold text-gray-800 mb-3">{hospital}</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Total Bills:</span>
                        <span className="text-lg font-bold text-indigo-600">{stats.count}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Total Amount:</span>
                        <span className="text-2xl font-bold text-green-600">${stats.total.toFixed(2)}</span>
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

            {selectedPatient && (
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
          </CardContent>
        </Card>

        {/* Bill Creation */}
        {selectedPatient && (
          <Card className="border-green-200 shadow-md">
            <CardHeader className="bg-gradient-to-r from-green-50 to-green-100 border-b border-green-200">
              <CardTitle className="flex items-center gap-2 text-green-900">
                <FileText className="w-5 h-5" />
                Create New Bill
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div className="flex gap-3">
                <div className="flex-1">
                  <Label className="text-gray-700 font-medium mb-2 block">Select Service/Drug</Label>
                  <Select value={selectedItem} onValueChange={setSelectedItem}>
                    <SelectTrigger data-testid="item-select" className="h-11 border-gray-300">
                      <SelectValue placeholder="Choose an item" />
                    </SelectTrigger>
                    <SelectContent>
                      {priceList.map((item) => (
                        <SelectItem key={item.item_id} value={item.item_id}>
                          {item.item_name} - ${item.cost.toFixed(2)} ({item.item_type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
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

              {billItems.length > 0 && (
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
                    <table className="w-full" data-testid="bill-items-table">
                      <thead className="bg-gray-100 border-b border-gray-200">
                        <tr>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">Item</th>
                          <th className="text-left p-3 text-sm font-semibold text-gray-700">Type</th>
                          <th className="text-right p-3 text-sm font-semibold text-gray-700">Cost</th>
                          <th className="text-center p-3 text-sm font-semibold text-gray-700">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {billItems.map((item, index) => (
                          <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="p-3 text-sm text-gray-800">{item.item_name}</td>
                            <td className="p-3 text-sm text-gray-600">{item.item_type}</td>
                            <td className="p-3 text-sm text-gray-800 text-right font-medium">${item.cost.toFixed(2)}</td>
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
                      Total: <span data-testid="total-bill-cost" className="text-blue-600">${getTotalBillCost().toFixed(2)}</span>
                    </div>
                    <Button
                      data-testid="submit-bill-button"
                      onClick={handleSubmitBill}
                      disabled={loading}
                      className="h-12 px-8 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold shadow-md"
                    >
                      Submit Bill
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Bill History */}
        <Card className="border-purple-200 shadow-md">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-purple-100 border-b border-purple-200">
            <CardTitle className="flex items-center gap-2 text-purple-900">
              <FileText className="w-5 h-5" />
              Recent Bills
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {bills.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No bills created yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full" data-testid="bills-table">
                  <thead className="bg-gray-100 border-b border-gray-200">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold text-gray-700">Bill ID</th>
                      <th className="text-left p-3 text-sm font-semibold text-gray-700">Patient</th>
                      <th className="text-left p-3 text-sm font-semibold text-gray-700">Date</th>
                      <th className="text-right p-3 text-sm font-semibold text-gray-700">Amount</th>
                      <th className="text-center p-3 text-sm font-semibold text-gray-700">Status</th>
                      <th className="text-center p-3 text-sm font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bills.map((bill) => (
                      <tr key={bill.bill_id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium text-gray-800">{bill.bill_id}</td>
                        <td className="p-3 text-sm text-gray-700">{bill.patient_name}</td>
                        <td className="p-3 text-sm text-gray-600">{new Date(bill.timestamp).toLocaleDateString()}</td>
                        <td className="p-3 text-sm text-gray-800 text-right font-medium">${bill.total_bill_amount.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                            bill.status === 'COMPLETED' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {bill.status}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Button
                              data-testid={`print-bill-${bill.bill_id}`}
                              onClick={() => handlePrintBill(bill.bill_id)}
                              variant="ghost"
                              size="sm"
                              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                            >
                              <Printer className="w-4 h-4" />
                            </Button>
                            {bill.status === 'COMPLETED' && (
                              <Button
                                data-testid={`void-bill-${bill.bill_id}`}
                                onClick={() => handleVoidBill(bill.bill_id)}
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Ban className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;