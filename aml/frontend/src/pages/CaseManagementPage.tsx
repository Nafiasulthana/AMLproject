import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Case } from '../types';
import { FolderLock, Plus, FileText, CheckCircle2, AlertOctagon, MessageSquare } from 'lucide-react';

export const CaseManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [noteText, setNoteText] = useState('');
  const [notesList, setNotesList] = useState<any[]>([]);

  const fetchCases = () => {
    api.get('/cases')
      .then(res => {
        setCases(res.data);
        if (res.data.length > 0 && !selectedCase) {
          handleSelectCase(res.data[0]);
        }
      });
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleSelectCase = (c: Case) => {
    setSelectedCase(c);
    api.get(`/cases/${c.case_id}`)
      .then(res => setNotesList(res.data.notes || []));
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase || !noteText.trim()) return;
    await api.post(`/cases/${selectedCase.case_id}/notes`, { note_text: noteText });
    setNoteText('');
    handleSelectCase(selectedCase);
  };

  const handleUpdateStatus = async (status: string) => {
    if (!selectedCase) return;
    await api.put(`/cases/${selectedCase.case_id}`, { status });
    fetchCases();
  };

  return (
    <div className="space-y-5 select-none">
      <div className="border-b border-[#202A35] pb-3">
        <h1 className="text-sm font-bold text-[#E8EDF2] tracking-tight flex items-center space-x-2">
          <FolderLock className="w-4 h-4 text-[#3B82F6]" />
          <span>AML Case Management Workbench</span>
        </h1>
        <p className="text-[11px] text-[#8995A3] mt-0.5">Multi-alert cross-typology case triaging, investigator logs, and STR filing pipeline</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Case List Sidebar */}
        <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35] space-y-2.5">
          <div className="text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-2 border-b border-[#202A35] pb-2">
            Active Investigation Cases ({cases.length})
          </div>
          {cases.map((c) => (
            <div
              key={c.case_id}
              onClick={() => handleSelectCase(c)}
              className={`p-3 rounded border cursor-pointer transition-colors ${
                selectedCase?.case_id === c.case_id
                  ? 'bg-[#151D26] border-[#3B82F6] text-[#E8EDF2]'
                  : 'bg-[#0B0F14] border-[#202A35] text-[#8995A3] hover:text-[#E8EDF2]'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold font-mono text-[#3B82F6]">{c.case_id}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${
                  c.priority === 'CRITICAL' ? 'bg-[#151D26] text-[#EF4444] border border-[#EF4444]/40' : 'bg-[#151D26] text-[#F59E0B] border border-[#F59E0B]/40'
                }`}>
                  {c.priority}
                </span>
              </div>
              <div className="text-xs font-semibold truncate text-[#E8EDF2]">{c.title}</div>
              <div className="text-[10px] font-mono text-[#5E6A78] mt-1 flex justify-between">
                <span>Meta Risk: {c.meta_risk_score}%</span>
                <span>{c.status}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Selected Case Workspace & Notes */}
        {selectedCase && (
          <div className="lg:col-span-2 space-y-5">
            <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35] space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#202A35]">
                <div>
                  <div className="text-xs font-mono text-[#3B82F6] font-bold">{selectedCase.case_id}</div>
                  <h2 className="text-sm font-bold text-[#E8EDF2]">{selectedCase.title}</h2>
                </div>

                <div className="flex items-center space-x-2">
                  {['OPEN', 'IN_REVIEW', 'ESCALATED', 'CLOSED_STR'].map((st) => (
                    <button
                      key={st}
                      onClick={() => handleUpdateStatus(st)}
                      className={`px-2.5 py-1 rounded text-[10px] font-bold transition-all ${
                        selectedCase.status === st
                          ? 'bg-[#3B82F6] text-white'
                          : 'bg-[#151D26] text-[#8995A3] border border-[#202A35] hover:text-[#E8EDF2]'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                  <button
                    onClick={() => navigate(`/str-reports?case=${selectedCase.case_id}`)}
                    className="px-3 py-1 bg-[#22C55E] hover:bg-[#16a34a] text-white font-semibold text-xs rounded flex items-center space-x-1"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Generate STR</span>
                  </button>
                </div>
              </div>

              <div className="text-xs text-[#B0BAC5] leading-relaxed bg-[#151D26] p-3 rounded border border-[#202A35]">
                <span className="font-bold text-[#E8EDF2]">Case Summary: </span>{selectedCase.summary}
              </div>

              {/* Add Investigation Note */}
              <div className="pt-3 border-t border-[#202A35] space-y-3">
                <div className="text-[10px] font-bold text-[#8995A3] uppercase tracking-wider flex items-center space-x-1.5">
                  <MessageSquare className="w-3.5 h-3.5 text-[#3B82F6]" />
                  <span>Investigator Timeline & Audit Notes</span>
                </div>

                <form onSubmit={handleAddNote} className="flex space-x-2">
                  <input
                    type="text"
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Enter official investigation note..."
                    className="flex-1 bg-[#151D26] border border-[#202A35] rounded px-3 py-1.5 text-xs text-[#E8EDF2] focus:outline-none focus:border-[#3B82F6]"
                  />
                  <button type="submit" className="px-3 py-1.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white text-xs font-semibold rounded">
                    Add Note
                  </button>
                </form>

                <div className="space-y-2 max-h-60 overflow-y-auto pt-1">
                  {notesList.map((note) => (
                    <div key={note.note_id} className="p-2.5 bg-[#151D26] rounded border border-[#202A35] text-xs">
                      <div className="flex justify-between text-[10px] text-[#5E6A78] font-mono mb-1">
                        <span className="text-[#3B82F6] font-bold">{note.author_name || 'Investigator'}</span>
                        <span>{new Date(note.created_at).toLocaleString()}</span>
                      </div>
                      <div className="text-[#B0BAC5]">{note.note_text}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
