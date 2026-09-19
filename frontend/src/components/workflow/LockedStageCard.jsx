import React from 'react';
import {
  Lock,
  ShieldAlert,
  BarChart,
  FileSpreadsheet,
  FileText,
  Bot,
  TrendingUp,
  Sparkles,
  Info
} from 'lucide-react';

export const FUTURE_STAGES = [
  {
    id: 'dpr_generator',
    stageNum: 13,
    pillar: 'Prepare',
    name: 'DPR Generator',
    icon: FileText,
    desc: 'Institutional-grade Detailed Project Report generation aligned with PMMY / PMEGP credit parameters.',
    badge: 'Stage 13 · Prepare'
  },
  {
    id: 'personal_ai_assistant',
    stageNum: 14,
    pillar: 'Grow',
    name: 'Personal AI Assistant',
    icon: Bot,
    desc: 'Multilingual conversational agent providing day-to-day regulatory, taxation, and operational advice in native vernacular.',
    badge: 'Stage 14 · Grow'
  },
  {
    id: 'growth_manager',
    stageNum: 15,
    pillar: 'Grow',
    name: 'Growth Manager',
    icon: TrendingUp,
    desc: 'Continuous performance tracking, working capital alerts, and supply chain expansion recommendations.',
    badge: 'Stage 15 · Grow'
  }
];

export default function LockedStageCard({ stage }) {
  const Icon = stage.icon || Lock;

  return (
    <div className="rounded-2xl p-6 border border-[#EAE3D5]/80 bg-white/70 backdrop-blur-md shadow-2xs flex flex-col justify-between relative overflow-hidden group hover:border-[#D97706]/40 transition-all">
      <div className="absolute top-0 right-0 bg-stone-100 border-b border-l border-[#EAE3D5] text-stone-500 text-[10px] font-bold px-3 py-1 rounded-bl-xl uppercase tracking-wider flex items-center gap-1">
        <Lock className="w-3 h-3 text-stone-400" />
        Future Stage
      </div>

      <div>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-9 h-9 rounded-xl bg-stone-100 border border-stone-200 flex items-center justify-center text-stone-500">
            <Icon className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C]">
            {stage.badge}
          </span>
        </div>

        <h4 className="text-base font-bold text-[#1C1917] font-['Outfit'] mb-1.5">
          {stage.name}
        </h4>
        <p className="text-xs text-[#57534E] leading-relaxed">
          {stage.desc}
        </p>
      </div>

      <div className="mt-5 pt-3 border-t border-[#EAE3D5]/70 flex items-center justify-between text-[11px] text-[#78716C]">
        <span className="flex items-center gap-1">
          <Info className="w-3 h-3 text-stone-400" />
          Unlocks in Phase 2
        </span>
        <span className="font-semibold text-stone-400">Locked Milestone</span>
      </div>
    </div>
  );
}
