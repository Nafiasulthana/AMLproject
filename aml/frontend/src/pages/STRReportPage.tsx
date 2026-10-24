import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { STRReport } from '../types';
import { FileText, Download, CheckCircle, Plus, ShieldCheck, Eye, X } from 'lucide-react';

export const STRReportPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const targetCaseId = searchParams.get('case') || 'CASE_1001';

  const [reports, setReports] = useState<STRReport[]>([]);
  const [narrative, setNarrative] = useState(
    'Formal Suspicious Transaction Report (STR) submitted regarding multi-hop layering transfers, CTR threshold structuring, and dormant account reactivation patterns detected across connected customer account network.'
  );
  const [loading, setLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const fetchReports = () => {
    api.get('/str')
      .then(res => setReports(res.data))
      .catch(() => {});
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/str/generate', {
        case_id: targetCaseId,
        narrative_summary: narrative
      });
      fetchReports();
      if (res.data?.report_id) {
        handlePreview(res.data.report_id);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate STR');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (reportId: string) => {
    await api.post(`/str/${reportId}/approve`);
    fetchReports();
  };

  const handlePreview = async (reportId: string) => {
    try {
      const response = await api.get(`/str/${reportId}/download`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      if (previewUrl) {
        window.URL.revokeObjectURL(previewUrl);
      }
      setPreviewUrl(url);
    } catch (err: any) {
      alert('Failed to load STR PDF preview');
    }
  };

  const handleDownload = async (reportId: string) => {
    try {
      const response = await api.get(`/str/${reportId}/download`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `STR_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      let detail = err.response?.data?.detail;
      if (!detail && err.response?.data instanceof Blob) {
        try {
          const text = await err.response.data.text();
          const parsed = JSON.parse(text);
          detail = parsed.detail;
        } catch {
          // ignore
        }
      }
      alert(detail || 'Failed to download STR report');
    }
  };

  return (
    <div className="space-y-5 select-none">
      <div className="border-b border-[#202A35] pb-3">
        <h1 className="text-sm font-bold text-[#E8EDF2] tracking-tight flex items-center space-x-2">
          <FileText className="w-4 h-4 text-[#94A3B8]" />
          <span>Financial Intelligence Unit (FIU) STR Filing Generator</span>
        </h1>
        <p className="text-[11px] text-[#8995A3] mt-0.5">Official Suspicious Transaction Report (STR) PDF compilation and Principal Officer sign-off module</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* STR Generation Form */}
        <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35] space-y-3">
          <h2 className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider flex items-center space-x-1.5 border-b border-[#202A35] pb-2">
            <Plus className="w-3.5 h-3.5 text-[#94A3B8]" />
            <span>Generate New STR Draft</span>
          </h2>

          <form onSubmit={handleGenerate} className="space-y-3">
            <div>
              <label className="block text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-1">Target Case ID</label>
              <input
                type="text"
                value={targetCaseId}
                readOnly
                className="w-full bg-[#151D26] border border-[#202A35] rounded px-3 py-1.5 text-xs text-[#E2E8F0] font-mono font-bold"
              />
            </div>

            <div>
              <label className="block text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-1">Investigative Narrative Summary</label>
              <textarea
                rows={5}
                value={narrative}
                onChange={(e) => setNarrative(e.target.value)}
                required
                className="w-full bg-[#151D26] border border-[#202A35] rounded p-2.5 text-xs text-[#E8EDF2] focus:outline-none focus:border-[#64748B]"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-[#334155] hover:bg-[#475569] text-white font-semibold text-xs rounded flex items-center justify-center space-x-1.5 transition-colors disabled:opacity-50 border border-[#475569]/50"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{loading ? 'Compiling PDF Report...' : 'Generate Official STR PDF'}</span>
            </button>
          </form>
        </div>

        {/* Existing STR Reports Table */}
        <div className="lg:col-span-2 bg-[#111820] p-4 rounded-lg border border-[#202A35] space-y-3">
          <h2 className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider border-b border-[#202A35] pb-2">Generated STR Filings Archive</h2>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-[#202A35] text-[10px] font-bold text-[#5E6A78] uppercase tracking-wider font-sans">
                  <th className="py-2 px-3">Report ID</th>
                  <th className="py-2 px-3">FIU Ref Number</th>
                  <th className="py-2 px-3">Case ID</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202A35]/60 text-[#E8EDF2]">
                {reports.map((r) => (
                  <tr key={r.report_id} className="hover:bg-[#151D26] transition-colors">
                    <td className="py-2 px-3 text-[#E2E8F0] font-bold">{r.report_id}</td>
                    <td className="py-2 px-3 text-[#B0BAC5]">{r.fiu_ref_number}</td>
                    <td className="py-2 px-3 text-[#5E6A78]">{r.case_id}</td>
                    <td className="py-2 px-3 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        r.status === 'APPROVED' ? 'bg-[#151D26] text-[#22C55E] border border-[#22C55E]/40' : 'bg-[#151D26] text-[#F59E0B] border border-[#F59E0B]/40'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right font-sans space-x-2">
                      {r.status === 'DRAFT' && (
                        <button
                          onClick={() => handleApprove(r.report_id)}
                          className="px-2 py-1 bg-[#151D26] text-[#22C55E] border border-[#22C55E]/40 hover:bg-[#22C55E]/10 rounded text-[10px]"
                        >
                          Approve
                        </button>
                      )}
                      <button
                        onClick={() => handlePreview(r.report_id)}
                        className="px-2 py-1 bg-[#151D26] text-[#94A3B8] border border-[#202A35] hover:border-[#94A3B8]/50 rounded text-[10px] inline-flex items-center space-x-1"
                        title="Preview PDF document"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Preview</span>
                      </button>
                      <button
                        onClick={() => handleDownload(r.report_id)}
                        className="px-2 py-1 bg-[#151D26] text-[#E2E8F0] border border-[#202A35] hover:border-[#E2E8F0]/50 rounded text-[10px] inline-flex items-center space-x-1"
                        title="Download PDF"
                      >
                        <Download className="w-3 h-3" />
                        <span>PDF</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* PDF Document Preview Modal */}
      {previewUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="bg-[#111820] border border-[#202A35] rounded-lg w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between p-3 border-b border-[#202A35] bg-[#151D26]">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-[#94A3B8]" />
                <span className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider">STR PDF Document Preview</span>
              </div>
              <button
                onClick={() => {
                  if (previewUrl) window.URL.revokeObjectURL(previewUrl);
                  setPreviewUrl(null);
                }}
                className="p-1 bg-[#1A232E] text-[#8995A3] hover:text-white rounded border border-[#202A35] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <iframe src={previewUrl} className="w-full flex-1 border-none bg-white" title="STR PDF Preview" />
          </div>
        </div>
      )}
    </div>
  );
};
