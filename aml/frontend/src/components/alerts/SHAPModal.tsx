import React from 'react';
import { X, Brain, AlertCircle } from 'lucide-react';
import { SHAPExplanation } from '../../types';

interface SHAPModalProps {
  isOpen: boolean;
  onClose: () => void;
  shapData: SHAPExplanation | null;
  alertId: string;
}

export const SHAPModal: React.FC<SHAPModalProps> = ({ isOpen, onClose, shapData, alertId }) => {
  if (!isOpen || !shapData) return null;

  return (
    <div className="fixed inset-0 z-50 bg-[#0B0F14]/80 backdrop-blur-sm flex items-center justify-center p-4 select-none font-sans">
      <div className="bg-[#111820] border border-[#202A35] rounded-lg max-w-xl w-full p-5 shadow-2xl relative">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-[#8995A3] hover:text-[#E8EDF2]"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-2 text-[#3B82F6] mb-1">
          <Brain className="w-4 h-4" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#E8EDF2]">XGBoost + SHAP Feature Attribution</h3>
        </div>
        <p className="text-[11px] text-[#8995A3] mb-4 border-b border-[#202A35] pb-2">
          Alert ID: <span className="font-mono text-[#3B82F6] font-semibold">{alertId}</span> • ML Probability: <span className="font-bold text-[#EF4444] font-mono">{shapData.prediction_probability}%</span>
        </p>

        <div className="space-y-2.5 mb-4 max-h-[350px] overflow-y-auto pr-1">
          <div className="text-[10px] font-bold text-[#5E6A78] uppercase tracking-wider">Feature Risk Contribution Breakdown</div>
          {shapData.shap_values.map((item, idx) => (
            <div key={idx} className="bg-[#151D26] p-3 rounded border border-[#202A35] flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <AlertCircle className={`w-3.5 h-3.5 ${item.contribution > 0 ? 'text-[#EF4444]' : 'text-[#22C55E]'}`} />
                <div>
                  <div className="text-xs font-semibold text-[#E8EDF2]">{item.label}</div>
                  <div className="text-[10px] text-[#5E6A78] font-mono">Symbol: {item.feature}</div>
                </div>
              </div>

              <div className="text-right">
                <div className={`text-xs font-bold font-mono ${item.contribution > 0 ? 'text-[#EF4444]' : 'text-[#22C55E]'}`}>
                  {item.contribution > 0 ? `+${item.contribution}%` : `${item.contribution}%`}
                </div>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold font-mono ${
                  item.impact === 'CRITICAL_RISK' ? 'bg-[#151D26] text-[#EF4444] border border-[#EF4444]/40' :
                  item.impact === 'HIGH_RISK' ? 'bg-[#151D26] text-[#F59E0B] border border-[#F59E0B]/40' :
                  'bg-[#151D26] text-[#3B82F6] border border-[#3B82F6]/40'
                }`}>
                  {item.impact}
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-[#151D26] p-3 rounded border border-[#202A35] text-[11px] text-[#B0BAC5] flex items-start space-x-2">
          <Brain className="w-3.5 h-3.5 mt-0.5 shrink-0 text-[#3B82F6]" />
          <div>
            <span className="font-bold text-[#E8EDF2]">Investigator Guidance:</span> SHAP TreeExplainer decomposed the non-linear decision boundary of XGBoost to quantify feature contribution. Positive factors push toward suspicious classification.
          </div>
        </div>
      </div>
    </div>
  );
};
