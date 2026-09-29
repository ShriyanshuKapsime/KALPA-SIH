import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Layers
} from 'lucide-react';
import { useLanguage, TranslatedText } from '../../context/LanguageContext';

// Category Visual Configuration in KALPA-integrated semantic palette
const CATEGORY_CONFIG = {
  strengths: {
    icon: CheckCircle2,
    badgeText: 'text-[#1B4D3E]',
    badgeBg: 'bg-[#EAF5EE]',
    badgeBorder: 'border-[#1B4D3E]/25',
    titleColor: 'text-[#1B4D3E]',
    borderColor: 'border-[#1B4D3E]/25',
    itemBorderColor: 'border-[#1B4D3E]/15',
    iconBg: 'bg-[#EAF5EE]',
    iconColor: 'text-[#1B4D3E]',
    idColor: 'text-[#1B4D3E]',
    evidenceBadgeBg: 'bg-[#EAF5EE]',
    evidenceTextColor: 'text-[#1B4D3E]',
  },
  weaknesses: {
    icon: AlertTriangle,
    badgeText: 'text-[#A05A35]',
    badgeBg: 'bg-[#FAF2E3]',
    badgeBorder: 'border-[#A05A35]/30',
    titleColor: 'text-[#A05A35]',
    borderColor: 'border-[#A05A35]/25',
    itemBorderColor: 'border-[#A05A35]/15',
    iconBg: 'bg-[#FAF2E3]',
    iconColor: 'text-[#A05A35]',
    idColor: 'text-[#A05A35]',
    evidenceBadgeBg: 'bg-[#FAF2E3]',
    evidenceTextColor: 'text-[#A05A35]',
  },
  opportunities: {
    icon: Lightbulb,
    badgeText: 'text-[#2C5282]',
    badgeBg: 'bg-[#F0F5FA]',
    badgeBorder: 'border-[#2C5282]/25',
    titleColor: 'text-[#2C5282]',
    borderColor: 'border-[#2C5282]/25',
    itemBorderColor: 'border-[#2C5282]/15',
    iconBg: 'bg-[#F0F5FA]',
    iconColor: 'text-[#2C5282]',
    idColor: 'text-[#2C5282]',
    evidenceBadgeBg: 'bg-[#F0F5FA]',
    evidenceTextColor: 'text-[#2C5282]',
  },
  threats: {
    icon: ShieldAlert,
    badgeText: 'text-[#9B2C2C]',
    badgeBg: 'bg-[#FFF5F5]',
    badgeBorder: 'border-[#9B2C2C]/25',
    titleColor: 'text-[#9B2C2C]',
    borderColor: 'border-[#9B2C2C]/25',
    itemBorderColor: 'border-[#9B2C2C]/15',
    iconBg: 'bg-[#FFF5F5]',
    iconColor: 'text-[#9B2C2C]',
    idColor: 'text-[#9B2C2C]',
    evidenceBadgeBg: 'bg-[#FFF5F5]',
    evidenceTextColor: 'text-[#9B2C2C]',
  },
};

/**
 * Strips raw backend Stage references and replaces with clean engine names
 */
export const cleanEvidenceString = (text) => {
  if (!text || typeof text !== 'string') return text || '';
  return text
    // Replace Stage 6/8 Market / Stage 6 & 8 / Stage 6 with Market
    .replace(/^Stage\s*(6\s*(&|\/)\s*8|6)\s*(Market(\s*Intelligence)?)?:?\s*/i, 'Market: ')
    .replace(/^Stage\s*8\s*(Opportunity(\s*Evaluation)?)?:?\s*/i, 'Opportunity: ')
    // Replace Stage 9 Finance / Stage 9 with Finance
    .replace(/^Stage\s*9\s*(Finance|Financial(\s*Model)?)?:?\s*/i, 'Finance: ')
    // Replace Stage 10 Entrepreneur / Stage 10 Readiness / Stage 10 Skills / Stage 10 Training
    .replace(/^Stage\s*10\s*(Entrepreneur(\s*Readiness)?|Readiness|Skills|Training)?:?\s*/i, (m, p1) => {
      if (p1 && p1.toLowerCase().includes('skill')) return 'Skills: ';
      if (p1 && p1.toLowerCase().includes('training')) return 'Training: ';
      if (p1 && p1.toLowerCase().includes('entrepreneur')) return 'Entrepreneur: ';
      return 'Readiness: ';
    })
    // Replace Stage 11 Risk with Risk
    .replace(/^Stage\s*11\s*(Risk(\s*Resilience|\s*Assessment)?)?:?\s*/i, 'Risk: ')
    // Replace Stage 12 Feasibility with Feasibility
    .replace(/^Stage\s*12\s*(Feasibility(\s*Engine)?)?:?\s*/i, 'Feasibility: ')
    // Replace Stage 3 Profile with Profile
    .replace(/^Stage\s*3\s*(Business\s*Profile|Profile)?:?\s*/i, 'Profile: ')
    // Any remaining "Stage X verified:" or "Stage X:"
    .replace(/\bStage\s*\d+(\s*(&|\/)\s*\d+)?\s*(verified|grounded|validated|confirmed)?:\s*/gi, '')
    .replace(/\bStage\s*\d+(\s*(&|\/)\s*\d+)?\b/gi, (match) => {
      const num = match.replace(/Stage\s*/i, '').trim();
      if (num === '6' || num === '6/8' || num === '6 & 8') return 'Market';
      if (num === '8') return 'Opportunity';
      if (num === '9') return 'Finance';
      if (num === '10') return 'Readiness';
      if (num === '11') return 'Risk';
      if (num === '12') return 'Feasibility';
      if (num === '13') return 'SWOT';
      if (num === '14') return 'DPR';
      return '';
    })
    .replace(/\s{2,}/g, ' ')
    .trim();
};

export const SwotQuadrantCard = ({
  category = 'strengths',
  title = 'STRENGTHS',
  subtitle = 'What is working in your favor',
  items = [],
  expandedItems = {},
  onToggleItem,
  formatStageName,
  formatVal,
  getDeterministicKey,
}) => {
  const { t } = useLanguage();
  const cfg = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.strengths;
  const CategoryIcon = cfg.icon;

  const seenKeys = new Set();

  return (
    <div className={`royal-card bg-[#FAF7F2] rounded-3xl p-6 border ${cfg.borderColor} shadow-xs space-y-5 flex flex-col justify-between`}>
      {/* Quadrant Header */}
      <div className="space-y-4">
        <div className={`flex items-center justify-between pb-3 border-b ${cfg.itemBorderColor}`}>
          <div className="flex items-center space-x-3">
            <div className={`p-2.5 ${cfg.iconBg} rounded-2xl ${cfg.iconColor} border ${cfg.badgeBorder}`}>
              <CategoryIcon className="w-5 h-5" />
            </div>
            <div>
              <h4 className={`text-base font-bold ${cfg.titleColor} font-['Outfit'] tracking-wide`}>
                <TranslatedText text={title} />
              </h4>
              <p className="text-[11px] text-[#79563F]">
                <TranslatedText text={subtitle} />
              </p>
            </div>
          </div>
          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${cfg.badgeBg} ${cfg.badgeText} border ${cfg.badgeBorder}`}>
            {items.length} {t('identified', 'Identified')}
          </span>
        </div>

        {/* Quadrant Items List */}
        <div className="space-y-3.5">
          {items.map((item, idx) => {
            const itemKey = getDeterministicKey ? getDeterministicKey(category, item, idx, seenKeys) : `swot-${category}-${idx}`;
            const isExpanded = Boolean(expandedItems[itemKey] || (item.id && expandedItems[item.id]));

            const priorityNorm = String(item.priority || 'HIGH').toUpperCase();
            let priorityBadgeClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25';
            if (priorityNorm === 'HIGH') {
              priorityBadgeClass = 'bg-[#FAF2E3] text-[#A05A35] border-[#A05A35]/30 font-bold';
            } else if (priorityNorm === 'LOW') {
              priorityBadgeClass = 'bg-[#FAF7F2] text-[#79563F]/80 border-[#79563F]/20';
            }

            return (
              <div
                key={itemKey}
                className={`bg-white rounded-2xl p-4 border ${cfg.itemBorderColor} space-y-3 shadow-2xs hover:border-[#79563F]/30 transition-all`}
              >
                {/* Header Row */}
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1 flex-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className={`text-[10px] font-mono font-bold ${cfg.idColor}`}>
                        {item.id || `${category.slice(0, 2).toUpperCase()}-${String(idx + 1).padStart(3, '0')}`}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-md border ${priorityBadgeClass}`}>
                        {priorityNorm} {t('impact', 'IMPACT')}
                      </span>
                      {item.source_stage && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md border bg-[#FAF2E3] text-[#79563F] border-[#79563F]/20">
                          <TranslatedText text={formatStageName ? formatStageName(item.source_stage) : cleanEvidenceString(item.source_stage)} />
                        </span>
                      )}
                    </div>
                    <h5 className="text-sm font-bold text-[#1C1917] leading-snug break-words">
                      <TranslatedText text={cleanEvidenceString(item.title)} />
                    </h5>
                  </div>
                  <button
                    type="button"
                    onClick={() => onToggleItem && onToggleItem(itemKey)}
                    className="p-1 text-[#79563F]/60 hover:text-[#1C1917] rounded-lg hover:bg-[#FAF2E3] transition cursor-pointer flex-shrink-0"
                    title={isExpanded ? t('collapseDetails', 'Collapse details') : t('expandDetails', 'Expand details')}
                    aria-label={isExpanded ? t('collapseDetails', 'Collapse details') : t('expandDetails', 'Expand details')}
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>

                {/* Explanation */}
                <p className="text-xs text-[#28231F] leading-relaxed break-words">
                  <TranslatedText text={cleanEvidenceString(item.explanation || item.statement)} />
                </p>

                {/* Expandable Details & Upstream Evidence */}
                {isExpanded && (
                  <div className="pt-2 border-t border-[#79563F]/12 space-y-2 text-xs animate-fadeIn">
                    {item.why_it_matters && item.why_it_matters !== item.explanation && (
                      <div className="bg-[#FAF7F2] rounded-xl p-3 border border-[#79563F]/15 space-y-1">
                        <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider">
                          {t('whyThisMatters', 'Why This Matters:')}
                        </span>
                        <p className="text-[11px] text-[#28231F] leading-relaxed break-words">
                          <TranslatedText text={cleanEvidenceString(item.why_it_matters)} />
                        </p>
                      </div>
                    )}

                    {item.evidence && item.evidence.length > 0 && (
                      <div className={`${cfg.badgeBg} rounded-xl p-3 border ${cfg.badgeBorder} space-y-1.5`}>
                        <span className={`text-[10px] font-bold ${cfg.badgeText} uppercase flex items-center space-x-1`}>
                          <Layers className="w-3 h-3" />
                          <span>{t('upstreamGroundedEvidence', 'Upstream Grounded Evidence:')}</span>
                        </span>
                        {item.evidence.map((ev, eIdx) => (
                          <div
                            key={`ev-${category}-${item.id || idx}-${eIdx}`}
                            className={`text-[11px] ${cfg.badgeText} flex flex-wrap items-center gap-1.5 break-words`}
                          >
                            {typeof ev === 'string' ? (
                              <span className="font-semibold text-[#1C1917]">
                                • <TranslatedText text={cleanEvidenceString(ev)} />
                              </span>
                            ) : (
                              <>
                                <span className="font-bold px-1.5 py-0.5 rounded bg-white text-[#1C1917] border border-[#79563F]/15 text-[10px]">
                                  <TranslatedText text={formatStageName ? formatStageName(ev.source_stage) : cleanEvidenceString(ev.source_stage || 'Engine')} />
                                </span>
                                <span className="text-[#79563F]/60">→</span>
                                <span className="font-mono text-[10px] text-[#79563F]">
                                  <TranslatedText text={cleanEvidenceString(ev.source_field)} />
                                </span>
                                {ev.value !== undefined && ev.value !== null && (
                                  <span className="font-semibold text-[#1C1917]">
                                    = {formatVal ? formatVal(ev.value) : String(ev.value)}
                                  </span>
                                )}
                              </>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SwotQuadrantCard;
