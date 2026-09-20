import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Sparkles, Compass, CheckCircle2 } from 'lucide-react';
import AssistantWidget from '../../components/assistant/AssistantWidget';
import Button from '../../components/ui/Button';

export const AssistantPage = () => {
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Top Breadcrumb / Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-stone-500">
          <Link to="/journey" className="hover:text-amber-700 transition-colors">
            Journey
          </Link>
          <span>/</span>
          <Link to="/swot" className="hover:text-amber-700 transition-colors">
            Stage 13 SWOT
          </Link>
          <span>/</span>
          <span className="text-stone-800 font-semibold">Stage 15 Personal AI Business Assistant</span>
        </div>

        <Link to="/swot">
          <Button variant="outline" size="sm" icon={ArrowLeft}>
            Back to SWOT Matrix
          </Button>
        </Link>
      </div>

      {/* Hero Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-stone-900 via-stone-800 to-amber-950 p-6 rounded-3xl text-white shadow-lg">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
              STAGE 15 • PERSONAL BUSINESS ADVISOR
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight font-['Outfit']">
            AI Advisory & Livelihood Navigation
          </h1>
          <p className="text-xs text-stone-300 max-w-2xl">
            Conversational advisory grounded in your pipeline outputs across market intelligence, financial feasibility, risk models, and government schemes.
          </p>
        </div>
      </div>

      {/* Full Assistant Chat Component */}
      <AssistantWidget isEmbedded={false} />
    </div>
  );
};

export default AssistantPage;
