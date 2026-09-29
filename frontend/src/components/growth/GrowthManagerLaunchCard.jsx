import React, { useState } from 'react';
import { TrendingUp, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

export const GrowthManagerLaunchCard = ({
  businessId,
  sessionId,
  scenarioId,
  initialBusinessName = '',
  onContinueTransition = null,
  isTransitioning = false,
}) => {
  const { t } = useLanguage();

  // Neutral unselected initial state (neither launched nor planning preselected)
  const [isLaunched, setIsLaunched] = useState(null);
  const [confirmedBusinessName, setConfirmedBusinessName] = useState(() => {
    return initialBusinessName || sessionStorage.getItem('kalpa_business_name') || '';
  });

  const handleContinue = () => {
    if (isTransitioning) return;
    const finalBizName = (confirmedBusinessName || '').trim() || initialBusinessName || 'My Enterprise';
    sessionStorage.setItem('kalpa_business_name', finalBizName);
    sessionStorage.setItem('kalpa_business_launched', 'true');

    if (onContinueTransition) {
      onContinueTransition({
        businessId,
        sessionId,
        scenarioId,
        businessName: finalBizName,
      });
    }
  };

  return (
    <div className="growth-manager-launch-card bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-6 sm:p-7 shadow-2xs space-y-5 animate-fadeIn">
      {/* Block Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30 flex items-center justify-center shrink-0">
          <TrendingUp className="w-5 h-5 text-[#1B4D3E]" />
        </div>
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[#1C1917] font-['Outfit']">
            Ready to grow your business?
          </h2>
          <p className="text-xs text-[#79563F] mt-0.5">
            Transition from bank planning &amp; DPR synthesis into day-to-day operations and growth management.
          </p>
        </div>
      </div>

      {/* Launch Question & Dual Toggle */}
      <div className="bg-[#FAF7F2] border border-[#79563F]/20 rounded-2xl p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <span className="text-xs font-bold text-[#1C1917]">
            Is your enterprise officially launched or active?
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={isTransitioning}
              onClick={() => setIsLaunched(true)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                isLaunched === true
                  ? 'bg-[#1B4D3E] text-white shadow-2xs'
                  : 'bg-white text-[#79563F] border border-[#79563F]/30 hover:bg-[#FAF2E3]'
              }`}
            >
              Yes, Launched / Active
            </button>
            <button
              type="button"
              disabled={isTransitioning}
              onClick={() => setIsLaunched(false)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                isLaunched === false
                  ? 'bg-[#79563F] text-white shadow-2xs'
                  : 'bg-white text-[#79563F] border border-[#79563F]/30 hover:bg-[#FAF2E3]'
              }`}
            >
              Not Yet (in Planning)
            </button>
          </div>
        </div>

        {/* State 1: Explicitly Launched */}
        {isLaunched === true && (
          <div className="space-y-4 pt-3 border-t border-[#79563F]/15 animate-fadeIn">
            {/* Restrained Post-Launch Banner */}
            <div className="p-4 rounded-xl bg-[#EAF5EE] border border-[#1B4D3E]/30 text-[#1B4D3E] text-xs font-medium leading-relaxed flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-[#1B4D3E] shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-sm text-[#1B4D3E] mb-0.5">
                  Your business is ready for post-launch operations.
                </p>
                <p>
                  Your KALPA Growth Manager is ready to help you monitor cash flow, inventory, supplier obligations, and demand signals.
                </p>
              </div>
            </div>

            {/* Business Name Field */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-[#79563F] uppercase tracking-wider">
                What is your business name?
              </label>
              <input
                type="text"
                value={confirmedBusinessName}
                onChange={(e) => setConfirmedBusinessName(e.target.value)}
                placeholder="e.g. Kamadhenu Dairy & Milk Production"
                className="w-full px-4 py-2.5 rounded-xl bg-white border border-[#79563F]/30 text-sm font-semibold text-[#1C1917] focus:outline-none focus:ring-2 focus:ring-[#79563F]/25"
              />
              <p className="text-[11px] text-[#79563F]/80">
                Prefilled from validated DPR profile. You can edit this anytime.
              </p>
            </div>

            {/* Feature Highlights Card */}
            <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 sm:p-5 space-y-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F]">
                  KALPA Growth Manager
                </span>
                <h4 className="text-sm font-bold text-[#1C1917] mt-0.5 font-['Outfit']">
                  Your post-launch business operating assistant
                </h4>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs text-[#79563F]">
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Monitor inventory &amp; stock levels</span>
                </div>
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Track sales and operating expenses</span>
                </div>
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Monitor cash flow and margins</span>
                </div>
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Track supplier payments &amp; delays</span>
                </div>
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Track bank EMI obligations</span>
                </div>
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Add products using photo or voice</span>
                </div>
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Identify business risks early</span>
                </div>
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Sell through digital channels &amp; ONDC</span>
                </div>
                <div className="flex items-start gap-2 bg-[#FAF7F2] p-2.5 rounded-xl border border-[#79563F]/15">
                  <span className="text-[#1B4D3E] font-bold shrink-0">✓</span>
                  <span>Get practical business guidance</span>
                </div>
              </div>

              <div className="pt-3 flex justify-end">
                <button
                  type="button"
                  disabled={isTransitioning}
                  onClick={handleContinue}
                  className={`saffron-gradient-btn px-6 py-3 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 shadow-xs transition-all ${
                    isTransitioning ? 'opacity-70 cursor-wait' : 'cursor-pointer hover:scale-[1.02]'
                  }`}
                >
                  <span>{isTransitioning ? 'Transitioning Operating Mode...' : 'Continue to KALPA Growth Manager'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* State 2: Explicitly In Planning */}
        {isLaunched === false && (
          <div className="p-4 rounded-xl bg-[#FAF2E3] border border-[#79563F]/20 text-xs text-[#79563F] space-y-1.5 animate-fadeIn">
            <p className="font-semibold text-[#1C1917]">
              Preparing for launch?
            </p>
            <p>
              Download your institutional DPR above to present to bank lenders or credit committees. Once your enterprise is active, return anytime to access KALPA Growth Manager.
            </p>
          </div>
        )}

        {/* State 3: Neutral Initial State */}
        {isLaunched === null && (
          <div className="p-3.5 rounded-xl bg-[#FAF2E3]/60 border border-[#79563F]/15 text-xs text-[#79563F] flex items-center justify-between">
            <span>Please select whether your business is active or currently in planning.</span>
            <span className="text-[11px] font-semibold text-[#79563F]/70">Selection required</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default GrowthManagerLaunchCard;
