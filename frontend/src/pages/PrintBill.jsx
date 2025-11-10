import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Printer, Activity } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PrintBill = () => {
  const { claimId } = useParams();
  const [claimData, setClaimData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBillData();
  }, [claimId]);

  const loadBillData = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
      return;
    }

    try {
      const response = await axios.get(`${API}/claims/${claimId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClaimData(response.data);
    } catch (error) {
      alert('Failed to load claim data');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-600">Loading claim...</div>
      </div>
    );
  }

  if (!claimData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-600">Claim not found</div>
      </div>
    );
  }

  const { header, details } = claimData;

  return (
    <div className="min-h-screen bg-gray-50 p-8 print:p-0 print:bg-white">
      <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden print:shadow-none print:rounded-none">
        {/* Print Button */}
        <div className="p-4 bg-blue-600 print:hidden flex items-center justify-between">
          <Button
            onClick={handlePrint}
            className="bg-white text-blue-600 hover:bg-gray-100 font-semibold"
            data-testid="print-button"
          >
            <Printer className="w-4 h-4 mr-2" />
            Print Bill
          </Button>
          <Button
            onClick={() => window.close()}
            variant="outline"
            className="bg-white text-blue-600 hover:bg-gray-100 font-semibold"
          >
            Close
          </Button>
        </div>

        {/* Bill Content */}
        <div className="p-8 print:p-6" data-testid="print-bill-content">
          {/* Header */}
          <div className="flex items-center justify-between mb-8 pb-6 border-b-2 border-blue-600">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-blue-600 p-2 rounded-lg">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-3xl font-bold text-gray-800">Medical Insurance</h1>
              </div>
              <p className="text-lg text-gray-600 font-medium">{header.hospital_name}</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Claim ID</div>
              <div className="text-xl font-bold text-gray-800" data-testid="bill-id">{header.claim_id}</div>
              <div className="text-sm text-gray-600 mt-2">{new Date(header.timestamp).toLocaleString()}</div>
            </div>
          </div>

          {/* Patient Info */}
          <div className="mb-8 bg-blue-50 p-6 rounded-lg border border-blue-200">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Patient Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Patient Name:</span>
                <div className="font-semibold text-gray-800" data-testid="bill-patient-name">{header.patient_name}</div>
              </div>
              <div>
                <span className="text-sm text-gray-600">Serial Number:</span>
                <div className="font-semibold text-gray-800">{header.patient_serial_number}</div>
              </div>
              <div>
                <span className="text-sm text-gray-600">Family ID:</span>
                <div className="font-semibold text-gray-800">{header.family_id}</div>
              </div>
              <div>
                <span className="text-sm text-gray-600">Status:</span>
                <div>
                  <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                    header.status === 'COMPLETED' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {header.status}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Bill Items */}
          <div className="mb-8">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Services & Medications</h2>
            <table className="w-full border border-gray-200">
              <thead className="bg-gray-100">
                <tr>
                  <th className="text-left p-3 border-b border-gray-200 font-semibold text-gray-700">Item Name</th>
                  <th className="text-right p-3 border-b border-gray-200 font-semibold text-gray-700">Unit Cost</th>
                  <th className="text-center p-3 border-b border-gray-200 font-semibold text-gray-700">Quantity</th>
                  <th className="text-right p-3 border-b border-gray-200 font-semibold text-gray-700">Total</th>
                </tr>
              </thead>
              <tbody data-testid="bill-items-list">
                {details.map((item, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="p-3 text-gray-800">{item.item_name}</td>
                    <td className="p-3 text-right text-gray-600">${item.item_cost.toFixed(2)}</td>
                    <td className="p-3 text-center font-medium text-gray-800">{item.quantity || 1}</td>
                    <td className="p-3 text-right font-bold text-gray-800">${(item.item_cost * (item.quantity || 1)).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-blue-50">
                <tr>
                  <td className="p-4 font-bold text-gray-800 text-lg">Total Amount</td>
                  <td className="p-4 text-right font-bold text-blue-600 text-xl" data-testid="bill-total">${header.total_claim_amount.toFixed(2)}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Footer */}
          <div className="text-center text-sm text-gray-600 pt-6 border-t border-gray-200">
            <p>This is a computer-generated bill and does not require a signature.</p>
            <p className="mt-2">Thank you for choosing {header.hospital_name}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrintBill;