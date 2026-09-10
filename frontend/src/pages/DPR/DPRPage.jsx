import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Lock, ArrowLeft } from 'lucide-react';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';

export const DPRPage = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      <div className="space-y-2 text-center max-w-xl mx-auto">
        <Badge variant="locked" className="mb-2">
          <Lock className="w-3 h-3 mr-1" /> Upcoming in Phase 2
        </Badge>
        <h1 className="text-3xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
          Bankable Detailed Project Report (DPR)
        </h1>
        <p className="text-sm text-[#57534E]">
          Automated generation of institutional-grade DPRs aligned with PMMY / PMEGP credit guidelines.
        </p>
      </div>

      <div className="royal-card rounded-3xl p-8 text-center space-y-6 max-w-lg mx-auto border-2 border-stone-200">
        <div className="w-14 h-14 rounded-2xl bg-stone-100 text-stone-600 flex items-center justify-center mx-auto">
          <FileText className="w-7 h-7 text-[#EA580C]" />
        </div>

        <div className="space-y-2">
          <h3 className="text-lg font-bold text-[#1C1917]">DPR Generator Locked</h3>
          <p className="text-xs text-[#78716C] leading-relaxed">
            Detailed project reports are synthesized in the final stage after market intelligence and feasibility modeling are complete.
          </p>
        </div>

        <Link to="/intake" className="inline-block">
          <Button size="md" icon={ArrowLeft}>
            Go to Stage 1 Intake
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default DPRPage;
