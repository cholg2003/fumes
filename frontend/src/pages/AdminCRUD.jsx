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
import { ArrowLeft, Plus, Edit, Trash2, Building2, Users, UserPlus, UsersRound, FileText, Receipt, Printer, Ban, CheckCircle, Key, Search, Upload, Download, DollarSign } from 'lucide-react';

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
  const [currencies, setCurrencies] = useState([]);

  const [loading, setLoading] = useState(false);

  // Dialog states
  const [hospitalDialog, setHospitalDialog] = useState(false);
  const [userDialog, setUserDialog] = useState(false);
  const [familyDialog, setFamilyDialog] = useState(false);
  const [bulkFamilyDialog, setBulkFamilyDialog] = useState(false);
  const [memberDialog, setMemberDialog] = useState(false);
  const [pricelistDialog, setPricelistDialog] = useState(false);
  const [currencyDialog, setCurrencyDialog] = useState(false);

  const [claimDialog, setClaimDialog] = useState(false);
  const [resetPasswordDialog, setResetPasswordDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [tempPassword, setTempPassword] = useState('');
  const [depositDialog, setDepositDialog] = useState(false);
  const [selectedHospital, setSelectedHospital] = useState(null);
  const [depositAmount, setDepositAmount] = useState('');
  
  // CSV upload state
  const [csvFile, setCsvFile] = useState(null);
  const [csvData, setCsvData] = useState([]);
  const [uploadResult, setUploadResult] = useState(null);

  // Forms
  const [hospitalForm, setHospitalForm] = useState({ hospital_name: '', address: '', phone: '', email: '', currency_code: 'USD' });
  const [userForm, setUserForm] = useState({ username: '', hospital_name: '', role: 'Billing Clerk', temporary_password: '', first_login: true });
  const [familyForm, setFamilyForm] = useState({ family_id: '', principle_member_name: '', total_allotment: '', remaining_balance: '' });
  const [memberForm, setMemberForm] = useState({ serial_number: '', family_id: '', first_name: '', middle_name: '', last_name: '', dob: '', sex: 'Male', relationship: 'Principle' });
  const [pricelistForm, setPricelistForm] = useState({ hospital_name: '', item_id: '', item_name: '', item_type: 'Service', cost: '' });
  const [currencyForm, setCurrencyForm] = useState({ code: '', name: '', symbol: '', rate_to_usd: '', decimal_places: 2 });

  
  // Claim edit form
  const [claimForm, setClaimForm] = useState({ claim_id: '', patient_serial_number: '', claim_items: [] });
  const [selectedClaimItem, setSelectedClaimItem] = useState('');
  const [claimItemQuantity, setClaimItemQuantity] = useState(1);

  // Search states
  const [hospitalSearch, setHospitalSearch] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [familySearch, setFamilySearch] = useState('');
  const [memberSearch, setMemberSearch] = useState('');
  const [pricelistSearch, setPricelistSearch] = useState('');
  const [claimSearch, setClaimSearch] = useState('');
  const [currencySearch, setCurrencySearch] = useState('');

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
        axios.get(`${API}/admin/pricelists/all`, axiosConfig),
        axios.get(`${API}/currencies`, axiosConfig)
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
        setCurrencies(responses[5].data);
        setClaims(responses[6].data);
      } else {
        setFamilies(responses[0].data);
        setMembers(responses[1].data);
        setPricelists(responses[2].data);
        setCurrencies(responses[3].data);
        setClaims(responses[4].data);
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
      setHospitalForm({ hospital_name: '', address: '', phone: '', email: '', currency_code: 'USD' });
      setEditMode({ type: '', data: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  // Filter functions
  const filteredHospitals = hospitals.filter(h => 
    h.hospital_name.toLowerCase().includes(hospitalSearch.toLowerCase()) ||
    h.address.toLowerCase().includes(hospitalSearch.toLowerCase())
  );

  const filteredUsers = users.filter(u =>
    u.username.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.hospital_name.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.role.toLowerCase().includes(userSearch.toLowerCase())
  );

  const filteredFamilies = families.filter(f =>
    f.family_id.toLowerCase().includes(familySearch.toLowerCase()) ||
    f.principle_member_name.toLowerCase().includes(familySearch.toLowerCase())
  );

  const filteredMembers = members.filter(m =>
    m.serial_number.toLowerCase().includes(memberSearch.toLowerCase()) ||
    m.first_name.toLowerCase().includes(memberSearch.toLowerCase()) ||
    m.last_name.toLowerCase().includes(memberSearch.toLowerCase()) ||
    m.family_id.toLowerCase().includes(memberSearch.toLowerCase())
  );

  const filteredPricelists = pricelists.filter(p =>
    p.item_id.toLowerCase().includes(pricelistSearch.toLowerCase()) ||
    p.item_name.toLowerCase().includes(pricelistSearch.toLowerCase()) ||
    p.hospital_name.toLowerCase().includes(pricelistSearch.toLowerCase())
  );

  const filteredClaims = claims.filter(c =>
    c.claim_id.toLowerCase().includes(claimSearch.toLowerCase()) ||
    c.patient_name.toLowerCase().includes(claimSearch.toLowerCase()) ||
    c.hospital_name.toLowerCase().includes(claimSearch.toLowerCase())
  );

  const filteredCurrencies = currencies.filter(c =>
    c.code.toLowerCase().includes(currencySearch.toLowerCase()) ||
    c.name.toLowerCase().includes(currencySearch.toLowerCase())
  );

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

  const openResetPasswordDialog = (user) => {
    setSelectedUser(user);
    setTempPassword('');
    setResetPasswordDialog(true);
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    if (!tempPassword || tempPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      await axios.post(
        `${API}/admin/users/${selectedUser.username}/reset-password`,
        { temporary_password: tempPassword },
        axiosConfig
      );
      toast.success(`Password reset for ${selectedUser.username}. User must change password on next login.`);
      setResetPasswordDialog(false);
      setTempPassword('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    } finally {
      setLoading(false);
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
    if (!window.confirm(`Delete family "${familyId}"? This will fail if the family has members or bills.`)) return;
    try {
      await axios.delete(`${API}/admin/families/${familyId}`, axiosConfig);
      toast.success('Family deleted successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete family');
    }
  };

  // CSV Bulk Upload for Families
  const downloadCSVTemplate = () => {
    const template = `family_id,principle_member_name,total_allotment,serial_number,first_name,middle_name,last_name,dob,sex,relationship
GS-2384,Yor Chan Awong,5000,GS-2384-00,Yor,Chan,Awong,1982-01-01,Male,Principle
GS-2384,Yor Chan Awong,5000,GS-2384-01,Abul,Chol,Dau,1989-01-01,Female,Spouse
GS-2384,Yor Chan Awong,5000,GS-2384-02,Khamisa,Yor,Chan,2000-01-01,Female,Child
GS-2384,Yor Chan Awong,5000,GS-2384-03,Ayul,Yor,Chan,2003-01-01,Male,Child
GS-3001,John Doe,7500,GS-3001-00,John,Michael,Doe,1980-01-15,Male,Principle
GS-3001,John Doe,7500,GS-3001-01,Jane,Marie,Doe,1982-03-20,Female,Spouse`;
    
    const blob = new Blob([template], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'family_bulk_upload_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('Template downloaded! Fill it with your family data.');
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setCsvFile(file);
      parseCSV(file);
    }
  };

  const parseCSV = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split('\n').filter(line => line.trim());
      const headers = lines[0].split(',').map(h => h.trim());
      
      const data = [];
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        const row = {};
        headers.forEach((header, index) => {
          row[header] = values[index];
        });
        data.push(row);
      }
      
      setCsvData(data);
      toast.success(`Parsed ${data.length} rows from CSV`);
    };
    reader.readAsText(file);
  };

  const handleBulkFamilyUpload = async () => {
    if (csvData.length === 0) {
      toast.error('No data to upload');
      return;
    }

    setLoading(true);
    setUploadResult(null);

    try {
      // Group data by family_id
      const familyGroups = {};
      csvData.forEach(row => {
        if (!familyGroups[row.family_id]) {
          const allotment = parseFloat(row.total_allotment);
          familyGroups[row.family_id] = {
            family_id: row.family_id,
            principle_member_name: row.principle_member_name,
            total_allotment: allotment,
            remaining_balance: allotment, // Automatically set equal to total_allotment
            members: []
          };
        }
        
        familyGroups[row.family_id].members.push({
          serial_number: row.serial_number, // Include serial number from CSV
          first_name: row.first_name,
          middle_name: row.middle_name || '',
          last_name: row.last_name,
          dob: row.dob,
          sex: row.sex,
          relationship: row.relationship
        });
      });

      // Upload each family
      const results = [];
      for (const familyData of Object.values(familyGroups)) {
        try {
          const response = await axios.post(`${API}/admin/families/bulk`, familyData, axiosConfig);
          results.push({ success: true, family: familyData.family_id, message: response.data.message });
        } catch (error) {
          results.push({ success: false, family: familyData.family_id, error: error.response?.data?.detail || 'Failed' });
        }
      }

      setUploadResult(results);
      
      const successCount = results.filter(r => r.success).length;
      const failCount = results.filter(r => !r.success).length;
      
      if (failCount === 0) {
        toast.success(`Successfully uploaded ${successCount} families!`);
        setCsvFile(null);
        setCsvData([]);
        setBulkFamilyDialog(false);
        loadData();
      } else {
        toast.warning(`Uploaded ${successCount} families, ${failCount} failed`);
      }
    } catch (error) {
      toast.error('Upload failed');
    } finally {
      setLoading(false);
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

  // Claim CRUD
  const openClaimEditDialog = async (claim) => {
    try {
      // Get claim details
      const response = await axios.get(`${API}/claims/${claim.claim_id}`, axiosConfig);
      setClaimForm({
        claim_id: claim.claim_id,
        patient_serial_number: response.data.header.patient_serial_number,
        status: response.data.header.status || 'PENDING',  // Include current status
        claim_items: response.data.details.map(item => ({
          item_id: item.item_id,
          item_name: item.item_name,
          cost: item.item_cost,  // Map item_cost to cost
          quantity: item.quantity || 1
        }))
      });
      setClaimDialog(true);
    } catch (error) {
      toast.error('Failed to load claim details');
    }
  };

  const handleAddClaimItem = () => {
    if (!selectedClaimItem) {
      toast.error('Please select an item');
      return;
    }
    const item = pricelists.find(p => p.item_id === selectedClaimItem);
    if (item) {
      setClaimForm({
        ...claimForm,
        claim_items: [...claimForm.claim_items, { ...item, quantity: claimItemQuantity, cost: item.cost }]
      });
      setSelectedClaimItem('');
      setClaimItemQuantity(1);
    }
  };

  const handleRemoveClaimItem = (index) => {
    const newItems = claimForm.claim_items.filter((_, i) => i !== index);
    setClaimForm({ ...claimForm, claim_items: newItems });
  };

  const getClaimTotal = () => {
    return claimForm.claim_items.reduce((sum, item) => sum + (item.cost * (item.quantity || 1)), 0);
  };

  const handleClaimUpdate = async (e) => {
    e.preventDefault();
    if (claimForm.claim_items.length === 0) {
      toast.error('Please add at least one item');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.put(`${API}/admin/claims/${claimForm.claim_id}`, {
        patient_serial_number: claimForm.patient_serial_number,
        status: claimForm.status,  // Include status
        claim_items: claimForm.claim_items.map(item => ({
          item_id: item.item_id,
          item_name: item.item_name,
          item_cost: item.cost,
          quantity: item.quantity || 1
        }))
      }, axiosConfig);
      toast.success(response.data.message || 'Claim updated successfully');
      setClaimDialog(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update claim');
    } finally {
      setLoading(false);
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

  // Currency CRUD
  const handleCurrencySubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const currencyData = {
        code: currencyForm.code.toUpperCase(),
        name: currencyForm.name,
        symbol: currencyForm.symbol,
        rate_to_usd: parseFloat(currencyForm.rate_to_usd),
        decimal_places: parseInt(currencyForm.decimal_places)
      };

      if (editMode.type === 'currency') {
        await axios.put(`${API}/admin/currencies/${editMode.data.code}`, currencyData, axiosConfig);
        toast.success('Currency updated successfully');
      } else {
        await axios.post(`${API}/admin/currencies`, currencyData, axiosConfig);
        toast.success('Currency created successfully');
      }
      setCurrencyDialog(false);
      setCurrencyForm({ code: '', name: '', symbol: '', rate_to_usd: '', decimal_places: 2 });
      setEditMode({ type: '', data: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCurrencyDelete = async (code) => {
    if (code === 'USD') {
      toast.error('Cannot delete USD - it is the base currency');
      return;
    }
    if (!window.confirm(`Delete currency "${code}"? This will fail if any hospital is using this currency.`)) return;
    try {
      await axios.delete(`${API}/admin/currencies/${code}`, axiosConfig);
      toast.success('Currency deleted successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete currency');
    }
  };

  // Bill delete
  const handleClaimDelete = async (claimId) => {
    if (!window.confirm(`Delete claim "${claimId}"? This will refund the amount if the claim was pending.`)) return;
    try {
      await axios.delete(`${API}/admin/claims/${claimId}`, axiosConfig);
      toast.success('Claim deleted successfully');
      loadData();
    } catch (error) {
      toast.error('Failed to delete claim');
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
      case 'currency':
        setCurrencyForm(data);
        setCurrencyDialog(true);
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
          <TabsList className={`grid w-full ${isSuperAdmin ? 'grid-cols-8' : 'grid-cols-5'} bg-white border border-gray-200 p-1 rounded-lg`}>
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
            <TabsTrigger value="currencies"><DollarSign className="w-4 h-4 mr-2" />Currencies</TabsTrigger>
            <TabsTrigger value="documentation"><FileText className="w-4 h-4 mr-2" />Documentation</TabsTrigger>
          </TabsList>

          {/* Hospitals Tab - Superadmin Only */}
          {isSuperAdmin && (
          <TabsContent value="hospitals">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Hospitals</CardTitle>
                <Dialog open={hospitalDialog} onOpenChange={setHospitalDialog}>
                  <DialogTrigger asChild>
                    <Button onClick={() => { setEditMode({ type: '', data: null }); setHospitalForm({ hospital_name: '', address: '', phone: '', email: '', currency_code: 'USD' }); }}>
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
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search hospitals by name or address..."
                      value={hospitalSearch}
                      onChange={(e) => setHospitalSearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {hospitalSearch && (
                    <p className="text-sm text-gray-500 mt-2">
                      Found {filteredHospitals.length} hospital(s)
                    </p>
                  )}
                </div>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Hospital Name</th>
                      <th className="text-left p-3 text-sm font-semibold">Address</th>
                      <th className="text-left p-3 text-sm font-semibold">Phone</th>
                      <th className="text-left p-3 text-sm font-semibold">Email</th>
                      <th className="text-right p-3 text-sm font-semibold">Deposit Balance</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredHospitals.map((hospital) => {
                      const balance = hospital.deposit_balance || 0;
                      return (
                        <tr key={hospital.hospital_name} className="border-b hover:bg-gray-50">
                          <td className="p-3 text-sm font-medium">{hospital.hospital_name}</td>
                          <td className="p-3 text-sm">{hospital.address}</td>
                          <td className="p-3 text-sm">{hospital.phone}</td>
                          <td className="p-3 text-sm">{hospital.email}</td>
                          <td className={`p-3 text-sm text-right font-semibold ${balance > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${balance.toFixed(2)}
                          </td>
                          <td className="p-3 text-center">
                            <div className="flex items-center justify-center gap-2">
                              <Button variant="ghost" size="sm" onClick={() => { setSelectedHospital(hospital); setDepositAmount(''); setDepositDialog(true); }} title="Add Deposit">
                                <Plus className="w-4 h-4 text-green-600" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => openEditDialog('hospital', hospital)}>
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleHospitalDelete(hospital.hospital_name)} className="text-red-600">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
          )}

          {/* Deposit Dialog */}
          <Dialog open={depositDialog} onOpenChange={setDepositDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Deposit to {selectedHospital?.hospital_name}</DialogTitle>
              </DialogHeader>
              <form onSubmit={async (e) => {
                e.preventDefault();
                if (!selectedHospital || !depositAmount) return;
                setLoading(true);
                try {
                  const response = await axios.post(
                    `${API}/admin/hospitals/${selectedHospital.hospital_name}/deposit`,
                    { amount: parseFloat(depositAmount) },
                    axiosConfig
                  );
                  toast.success(response.data.message);
                  setDepositDialog(false);
                  setDepositAmount('');
                  loadData(); // Reload hospitals to show updated balance
                } catch (error) {
                  toast.error(error.response?.data?.detail || 'Failed to add deposit');
                } finally {
                  setLoading(false);
                }
              }} className="space-y-4">
                <div>
                  <Label>Current Balance</Label>
                  <div className={`text-2xl font-bold ${(selectedHospital?.deposit_balance || 0) > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${(selectedHospital?.deposit_balance || 0).toFixed(2)}
                  </div>
                </div>
                <div>
                  <Label>Deposit Amount ($)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    placeholder="Enter amount"
                    required
                  />
                </div>
                {depositAmount && (
                  <div className="bg-blue-50 p-3 rounded">
                    <p className="text-sm text-gray-700">
                      New Balance: <span className="font-bold text-green-600">
                        ${((selectedHospital?.deposit_balance || 0) + parseFloat(depositAmount || 0)).toFixed(2)}
                      </span>
                    </p>
                  </div>
                )}
                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? 'Processing...' : 'Add Deposit'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>


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
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search users by username, hospital, or role..."
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {userSearch && (
                    <p className="text-sm text-gray-500 mt-2">
                      Found {filteredUsers.length} user(s)
                    </p>
                  )}
                </div>
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
                    {filteredUsers.map((user) => (
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
                            {isSuperAdmin && user.username !== 'superadmin' && (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => openResetPasswordDialog(user)} 
                                className="text-orange-600 hover:bg-orange-50"
                                title="Reset Password"
                              >
                                <Key className="w-4 h-4" />
                              </Button>
                            )}
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
                <Button variant="outline" onClick={() => { setCsvFile(null); setCsvData([]); setUploadResult(null); setBulkFamilyDialog(true); }}>
                  <Upload className="w-4 h-4 mr-2" />Bulk Upload (CSV)
                </Button>
                <Dialog open={familyDialog} onOpenChange={setFamilyDialog}>
                  <DialogTrigger asChild>
                    <span className="hidden"></span>
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
                {/* Bulk Family Upload Dialog */}
                <Dialog open={bulkFamilyDialog} onOpenChange={setBulkFamilyDialog}>
                  <DialogTrigger asChild>
                    <span className="hidden"></span>
                  </DialogTrigger>
                  <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>Bulk Family Upload</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-6">
                      {/* Template Download */}
                      <div className="border rounded-lg p-4 bg-blue-50">
                        <h3 className="font-semibold mb-2">Step 1: Download Template</h3>
                        <p className="text-sm text-gray-600 mb-3">
                          Download the CSV template and fill it with your family and member data.
                        </p>
                        <Button onClick={downloadCSVTemplate} variant="outline">
                          <Download className="w-4 h-4 mr-2" />
                          Download CSV Template
                        </Button>
                      </div>

                      {/* File Upload */}
                      <div className="border rounded-lg p-4">
                        <h3 className="font-semibold mb-2">Step 2: Upload CSV File</h3>
                        <div className="space-y-3">
                          <Input
                            type="file"
                            accept=".csv"
                            onChange={handleFileChange}
                            className="cursor-pointer"
                          />
                          {csvFile && (
                            <p className="text-sm text-green-600">
                              Selected: {csvFile.name}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Preview Data */}
                      {csvData.length > 0 && (
                        <div className="border rounded-lg p-4">
                          <h3 className="font-semibold mb-2">Step 3: Preview Data ({csvData.length} rows)</h3>
                          <div className="max-h-60 overflow-y-auto">
                            <table className="w-full text-sm">
                              <thead className="bg-gray-100 sticky top-0">
                                <tr>
                                  <th className="text-left p-2">Serial Number</th>
                                  <th className="text-left p-2">Family ID</th>
                                  <th className="text-left p-2">Member Name</th>
                                  <th className="text-left p-2">DOB</th>
                                  <th className="text-left p-2">Relationship</th>
                                </tr>
                              </thead>
                              <tbody>
                                {csvData.slice(0, 10).map((row, index) => (
                                  <tr key={index} className="border-b">
                                    <td className="p-2 font-mono text-xs">{row.serial_number}</td>
                                    <td className="p-2">{row.family_id}</td>
                                    <td className="p-2">{row.first_name} {row.last_name}</td>
                                    <td className="p-2">{row.dob}</td>
                                    <td className="p-2">{row.relationship}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {csvData.length > 10 && (
                              <p className="text-sm text-gray-500 mt-2">
                                Showing first 10 rows of {csvData.length} total rows
                              </p>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Upload Results */}
                      {uploadResult && (
                        <div className="border rounded-lg p-4">
                          <h3 className="font-semibold mb-2">Upload Results</h3>
                          <div className="space-y-2 max-h-40 overflow-y-auto">
                            {uploadResult.map((result, index) => (
                              <div key={index} className={`p-2 rounded text-sm ${
                                result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                <strong>{result.family}:</strong> {
                                  result.success ? result.message : result.error
                                }
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex justify-end gap-3">
                        <Button 
                          variant="outline" 
                          onClick={() => setBulkFamilyDialog(false)}
                        >
                          Cancel
                        </Button>
                        <Button 
                          onClick={handleBulkFamilyUpload}
                          disabled={loading || csvData.length === 0}
                        >
                          {loading ? 'Uploading...' : `Upload ${csvData.length} Families`}
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search families by Family ID or member name..."
                      value={familySearch}
                      onChange={(e) => setFamilySearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {familySearch && (
                    <p className="text-sm text-gray-500 mt-2">
                      Found {filteredFamilies.length} family/families
                    </p>
                  )}
                </div>
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
                    {filteredFamilies.map((family) => (
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
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search members by serial number, name, or family ID..."
                      value={memberSearch}
                      onChange={(e) => setMemberSearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {memberSearch && (
                    <p className="text-sm text-gray-500 mt-2">
                      Found {filteredMembers.length} member(s)
                    </p>
                  )}
                </div>
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
                    {filteredMembers.map((member) => (
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
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search by Item ID, item name, or hospital..."
                      value={pricelistSearch}
                      onChange={(e) => setPricelistSearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {pricelistSearch && (
                    <p className="text-sm text-gray-500 mt-2">
                      Found {filteredPricelists.length} item(s)
                    </p>
                  )}
                </div>
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
                    {filteredPricelists.map((item, index) => (
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
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search by Claim ID, patient name, or hospital..."
                      value={claimSearch}
                      onChange={(e) => setClaimSearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {claimSearch && (
                    <p className="text-sm text-gray-500 mt-2">
                      Found {filteredClaims.length} claim(s)
                    </p>
                  )}
                </div>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Claim ID</th>
                      <th className="text-left p-3 text-sm font-semibold">Hospital</th>
                      <th className="text-left p-3 text-sm font-semibold">Patient</th>
                      <th className="text-left p-3 text-sm font-semibold">Date</th>
                      <th className="text-right p-3 text-sm font-semibold">Amount</th>
                      <th className="text-center p-3 text-sm font-semibold">Status</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredClaims.map((claim) => (
                      <tr key={claim.claim_id} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium">{claim.claim_id}</td>
                        <td className="p-3 text-sm">{claim.hospital_name}</td>
                        <td className="p-3 text-sm">{claim.patient_name}</td>
                        <td className="p-3 text-sm">{new Date(claim.timestamp).toLocaleDateString()}</td>
                        <td className="p-3 text-sm text-right font-medium">${claim.total_claim_amount.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
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
                              variant="ghost" 
                              size="sm" 
                              onClick={() => openClaimEditDialog(claim)}
                              className="text-green-600 hover:bg-green-50"
                              title="Edit Claim"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => window.open(`/print/${claim.claim_id}`, '_blank')}
                              className="text-blue-600 hover:bg-blue-50"
                              title="Print Claim"
                            >
                              <Printer className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => handleClaimDelete(claim.claim_id)} 
                              className="text-red-600 hover:bg-red-50"
                              title="Delete Claim"
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

          {/* Currencies Tab - Superadmin Only */}
          {isSuperAdmin && (
          <TabsContent value="currencies">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Currency Management</CardTitle>
                <Dialog open={currencyDialog} onOpenChange={setCurrencyDialog}>
                  <DialogTrigger asChild>
                    <Button onClick={() => { setEditMode({ type: '', data: null }); setCurrencyForm({ code: '', name: '', symbol: '', rate_to_usd: '', decimal_places: 2 }); }}>
                      <Plus className="w-4 h-4 mr-2" />Add Currency
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editMode.type === 'currency' ? 'Edit Currency' : 'Add Currency'}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleCurrencySubmit} className="space-y-4">
                      <div>
                        <Label>Currency Code (e.g., USD, KSH, EUR)</Label>
                        <Input 
                          value={currencyForm.code} 
                          onChange={(e) => setCurrencyForm({...currencyForm, code: e.target.value.toUpperCase()})} 
                          placeholder="USD" 
                          maxLength={3}
                          required 
                          disabled={editMode.type === 'currency'} 
                        />
                      </div>
                      <div>
                        <Label>Currency Name</Label>
                        <Input 
                          value={currencyForm.name} 
                          onChange={(e) => setCurrencyForm({...currencyForm, name: e.target.value})} 
                          placeholder="US Dollar"
                          required 
                        />
                      </div>
                      <div>
                        <Label>Currency Symbol</Label>
                        <Input 
                          value={currencyForm.symbol} 
                          onChange={(e) => setCurrencyForm({...currencyForm, symbol: e.target.value})} 
                          placeholder="$"
                          required 
                        />
                      </div>
                      <div>
                        <Label>Exchange Rate to USD</Label>
                        <Input 
                          type="number" 
                          step="0.0001" 
                          min="0.0001"
                          value={currencyForm.rate_to_usd} 
                          onChange={(e) => setCurrencyForm({...currencyForm, rate_to_usd: e.target.value})} 
                          placeholder="1.0000"
                          required 
                        />
                        <p className="text-xs text-gray-500 mt-1">1 {currencyForm.code || 'XXX'} = {currencyForm.rate_to_usd || '?'} USD</p>
                      </div>
                      <div>
                        <Label>Decimal Places</Label>
                        <Input 
                          type="number" 
                          min="0" 
                          max="4"
                          value={currencyForm.decimal_places} 
                          onChange={(e) => setCurrencyForm({...currencyForm, decimal_places: e.target.value})} 
                          required 
                        />
                      </div>
                      <Button type="submit" disabled={loading} className="w-full">
                        {loading ? 'Saving...' : editMode.type === 'currency' ? 'Update' : 'Create'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <div className="mb-4 bg-blue-50 border border-blue-200 p-3 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> USD is the base currency. All exchange rates are defined relative to USD. You cannot delete USD.
                  </p>
                </div>
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search currencies by code or name..."
                      value={currencySearch}
                      onChange={(e) => setCurrencySearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  {currencySearch && (
                    <p className="text-sm text-gray-500 mt-2">
                      Found {filteredCurrencies.length} currency(ies)
                    </p>
                  )}
                </div>
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold">Code</th>
                      <th className="text-left p-3 text-sm font-semibold">Name</th>
                      <th className="text-left p-3 text-sm font-semibold">Symbol</th>
                      <th className="text-right p-3 text-sm font-semibold">Rate to USD</th>
                      <th className="text-center p-3 text-sm font-semibold">Decimal Places</th>
                      <th className="text-center p-3 text-sm font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCurrencies.map((currency) => (
                      <tr key={currency.code} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium">{currency.code}</td>
                        <td className="p-3 text-sm">{currency.name}</td>
                        <td className="p-3 text-sm">{currency.symbol}</td>
                        <td className="p-3 text-sm text-right">{currency.rate_to_usd.toFixed(4)}</td>
                        <td className="p-3 text-sm text-center">{currency.decimal_places}</td>
                        <td className="p-3 text-center">
                          <div className="flex justify-center gap-2">
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => openEditDialog('currency', currency)}
                            >
                              <Edit className="w-4 h-4 text-blue-600" />
                            </Button>
                            {currency.code !== 'USD' && (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => handleCurrencyDelete(currency.code)} 
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredCurrencies.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <DollarSign className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>{currencySearch ? 'No currencies match your search.' : 'No currencies found. Add your first currency.'}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          )}

          {/* Documentation Tab */}
          <TabsContent value="documentation">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  System Documentation & Workflow
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Quick Links */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    📚 Complete System Documentation
                  </h3>
                  <p className="text-gray-700 mb-4">
                    Access the complete 12-page system documentation including workflows, user roles, security matrix, and feature details.
                  </p>
                  <a 
                    href="/Medical_Insurance_System_Presentation.html" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <FileText className="w-5 h-5" />
                    Open Full Documentation
                  </a>
                </div>

                {/* Quick Reference */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-4 rounded-lg border border-gray-200">
                    <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                      👤 User Roles
                    </h4>
                    <ul className="text-sm space-y-2 text-gray-700">
                      <li><strong>Superadmin:</strong> Full system control, manages all hospitals</li>
                      <li><strong>Hospital Admin:</strong> Claims operations for their hospital</li>
                      <li><strong>Finance:</strong> View claims and financial reports</li>
                      <li><strong>Reception:</strong> Patient search and claim submission</li>
                    </ul>
                  </div>

                  <div className="bg-white p-4 rounded-lg border border-gray-200">
                    <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                      🔄 Claim Statuses
                    </h4>
                    <ul className="text-sm space-y-2 text-gray-700">
                      <li><span className="inline-block w-3 h-3 bg-yellow-400 rounded-full mr-2"></span><strong>PENDING:</strong> Service provided, awaiting payment</li>
                      <li><span className="inline-block w-3 h-3 bg-green-500 rounded-full mr-2"></span><strong>PAID:</strong> Insurance has paid hospital</li>
                      <li><span className="inline-block w-3 h-3 bg-red-500 rounded-full mr-2"></span><strong>VOIDED:</strong> Claim cancelled/rejected</li>
                    </ul>
                  </div>
                </div>

                {/* Workflow Overview */}
                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <h4 className="font-semibold text-gray-800 mb-4 text-lg">🔄 Complete Workflow</h4>
                  
                  <div className="space-y-4">
                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">1</div>
                      <div>
                        <h5 className="font-semibold text-gray-800">Initial Setup (Superadmin Only)</h5>
                        <p className="text-sm text-gray-600">Register hospitals, create families, add members, set up price lists</p>
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">2</div>
                      <div>
                        <h5 className="font-semibold text-gray-800">Patient Visit & Claim Creation</h5>
                        <p className="text-sm text-gray-600">Search patient → Select services → Submit claim → Status: PENDING</p>
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">3</div>
                      <div>
                        <h5 className="font-semibold text-gray-800">Financial Tracking</h5>
                        <p className="text-sm text-gray-600">View outstanding claims, hospital balances, and pending payments</p>
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">4</div>
                      <div>
                        <h5 className="font-semibold text-gray-800">Payment Process (Superadmin Only)</h5>
                        <p className="text-sm text-gray-600">Add deposit → Mark claims as paid → Balances automatically adjusted</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Key Features */}
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200">
                  <h4 className="font-semibold text-gray-800 mb-4 text-lg">✨ Key Features</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div className="flex items-start gap-2">
                      <span className="text-green-600">✅</span>
                      <span>Patient search and management</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-green-600">✅</span>
                      <span>Claim creation with item quantities</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-green-600">✅</span>
                      <span>Edit claim status with balance adjustments</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-green-600">✅</span>
                      <span>Hospital deposit management</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-green-600">✅</span>
                      <span>Bulk family upload via CSV</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-green-600">✅</span>
                      <span>Role-based access control</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-green-600">✅</span>
                      <span>Financial dashboards</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-green-600">✅</span>
                      <span>Suspend/unsuspend families/members</span>
                    </div>
                  </div>
                </div>

                {/* Access Control Notice */}
                <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                  <h4 className="font-semibold text-yellow-800 mb-2 flex items-center gap-2">
                    ⚠️ Access Control Notice
                  </h4>
                  <p className="text-sm text-yellow-800">
                    Only <strong>Superadmin</strong> can create/edit families, members, and price lists. 
                    Hospital Admin has read-only access to master data but can submit and view claims.
                  </p>
                </div>

                {/* Support Section */}
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <h4 className="font-semibold text-gray-800 mb-2">📞 Need Help?</h4>
                  <p className="text-sm text-gray-600">
                    For detailed workflows, status transition matrices, security guidelines, and troubleshooting, 
                    please refer to the complete documentation using the button above.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

        </Tabs>

        {/* Reset Password Dialog */}
        <Dialog open={resetPasswordDialog} onOpenChange={setResetPasswordDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Reset Password - {selectedUser?.username}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handlePasswordReset} className="space-y-4">
              <div>
                <Label>Temporary Password</Label>
                <Input
                  type="text"
                  value={tempPassword}
                  onChange={(e) => setTempPassword(e.target.value)}
                  placeholder="Enter temporary password"
                  required
                  minLength={6}
                  autoFocus
                />
                <p className="text-sm text-gray-500 mt-1">
                  User will be required to change this password on next login.
                </p>
              </div>
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={() => setResetPasswordDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Resetting...' : 'Reset Password'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Edit Claim Dialog */}
        <Dialog open={claimDialog} onOpenChange={setClaimDialog}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Claim - {claimForm.claim_id}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleClaimUpdate} className="space-y-6">
              {/* Patient Selection */}
              <div>
                <Label>Patient Serial Number</Label>
                <Select 
                  value={claimForm.patient_serial_number} 
                  onValueChange={(value) => setClaimForm({...claimForm, patient_serial_number: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Patient" />
                  </SelectTrigger>
                  <SelectContent>
                    {members.map((member) => (
                      <SelectItem key={member.serial_number} value={member.serial_number}>
                        {member.serial_number} - {member.first_name} {member.last_name} (Family: {member.family_id})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Claim Status */}
              <div>
                <Label>Claim Status</Label>
                <Select 
                  value={claimForm.status || 'PENDING'} 
                  onValueChange={(value) => setClaimForm({...claimForm, status: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PENDING">
                      <span className="inline-flex items-center gap-2">
                        <span className="w-3 h-3 bg-yellow-400 rounded-full"></span>
                        PENDING
                      </span>
                    </SelectItem>
                    <SelectItem value="PAID">
                      <span className="inline-flex items-center gap-2">
                        <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                        PAID
                      </span>
                    </SelectItem>
                    <SelectItem value="VOIDED">
                      <span className="inline-flex items-center gap-2">
                        <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                        VOIDED
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-600 mt-1">
                  Changing status will automatically adjust family and hospital balances
                </p>
              </div>

              {/* Items Section */}
              <div className="border rounded-lg p-4 space-y-4">
                <h3 className="font-semibold">Claim Items</h3>
                
                {/* Add Item */}
                <div className="flex gap-3">
                  <div className="flex-1">
                    <Select value={selectedClaimItem} onValueChange={setSelectedClaimItem}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Item" />
                      </SelectTrigger>
                      <SelectContent>
                        {pricelists.map((item) => (
                          <SelectItem key={item.item_id} value={item.item_id}>
                            {item.item_id} - {item.item_name} - ${item.cost.toFixed(2)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="w-24">
                    <Input
                      type="number"
                      min="1"
                      value={claimItemQuantity}
                      onChange={(e) => setClaimItemQuantity(parseInt(e.target.value) || 1)}
                      placeholder="Qty"
                    />
                  </div>
                  <Button type="button" onClick={handleAddClaimItem}>
                    <Plus className="w-4 h-4 mr-1" />
                    Add
                  </Button>
                </div>

                {/* Items Table */}
                {claimForm.claim_items.length > 0 && (
                  <table className="w-full border">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="text-left p-2 text-sm">Item</th>
                        <th className="text-right p-2 text-sm">Unit Cost</th>
                        <th className="text-center p-2 text-sm">Qty</th>
                        <th className="text-right p-2 text-sm">Total</th>
                        <th className="text-center p-2 text-sm">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {claimForm.claim_items.map((item, index) => (
                        <tr key={index} className="border-b">
                          <td className="p-2 text-sm">{item.item_name}</td>
                          <td className="p-2 text-sm text-right">${item.cost.toFixed(2)}</td>
                          <td className="p-2 text-sm text-center">{item.quantity || 1}</td>
                          <td className="p-2 text-sm text-right font-bold">${(item.cost * (item.quantity || 1)).toFixed(2)}</td>
                          <td className="p-2 text-center">
                            <Button 
                              type="button" 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => handleRemoveClaimItem(index)}
                              className="text-red-600"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-blue-50">
                      <tr>
                        <td colSpan="3" className="p-2 text-sm font-bold">Total:</td>
                        <td className="p-2 text-sm text-right font-bold text-blue-600">${getClaimTotal().toFixed(2)}</td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                )}
              </div>

              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={() => setClaimDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Updating...' : 'Update Claim'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AdminCRUD;
