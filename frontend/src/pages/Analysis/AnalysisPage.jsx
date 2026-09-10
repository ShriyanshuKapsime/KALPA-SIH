import React from 'react';
import { Link } from 'react-router-dom';
import { Network, Lock, ArrowLeft, Layers } from 'lucide-react';
import Card, { CardTitle, CardDescription } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';

export const AnalysisPage = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      <div className="space-y-2 text-center max-w-xl mx-auto">
        <Badge variant="locked" className="mb-2">
          <Lock className="w-3 h-3 mr-1" /> Upcoming in Stage 2
        </Badge>
        <h1 className="text-3xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
          Business Classification & Market Intelligence
        </h1>
        <p className="text-sm text-[#57534E]">
          National Industrial Classification (NIC) mapping and spatial analytics will activate in Stage 2.
        </p>
      </div>

      <div className="royal-card rounded-3xl p-8 text-center space-y-6 max-w-lg mx-auto border-2 border-stone-200">
        <div className="w-14 h-14 rounded-2xl bg-stone-100 text-stone-600 flex items-center justify-center mx-auto">
          <Network className="w-7 h-7 text-[#EA580C]" />
        </div>

        <div className="space-y-2">
          <h3 className="text-lg font-bold text-[#1C1917]">Stage 2 Locked</h3>
          <p className="text-xs text-[#78716C] leading-relaxed">
            The Business Classification Engine requires structured user intake profile from Stage 1 before running NIC mapping and spatial market evaluation.
          </p>
        </div>

        <Link to="/intake" className="inline-block">
          <Button size="md" icon={ArrowLeft}>
            Return to Stage 1 Intake
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default AnalysisPage;
