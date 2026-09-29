import React, { useMemo } from 'react';
import { CheckCircle2, ChevronRight, AlertCircle, Info, Sparkles, Table as TableIcon } from 'lucide-react';

/**
 * Sanitizes assistant responses to replace internal Stage numbers with clean engine names
 */
export function sanitizeAssistantText(text) {
  if (!text || typeof text !== 'string') return text || '';
  return text
    // Clean raw boolean/state variables leaking from backend
    .replace(/\bdpr_available:\s*(true|false)\b/gi, '')
    .replace(/\bloan_guidance_available:\s*(true|false)\b/gi, '')
    .replace(/\bbusiness_launched:\s*(true|false)\b/gi, '')
    .replace(/\bgrowth_manager_active:\s*(true|false)\b/gi, '')
    // Clean stage mentions cleanly without forcing trailing colons
    .replace(/\bStage\s*(6\s*(&|\/)\s*8|6)\s*(Market(\s*Intelligence)?)?:?\s*/gi, (m) => m.includes(':') ? 'Market Intelligence: ' : 'Market Intelligence ')
    .replace(/\bStage\s*8\s*(Opportunity(\s*Evaluation)?)?:?\s*/gi, (m) => m.includes(':') ? 'Opportunity Evaluation: ' : 'Opportunity Evaluation ')
    .replace(/\bStage\s*9\s*(Finance|Financial(\s*Model)?)?:?\s*/gi, (m) => m.includes(':') ? 'Financial Model: ' : 'Financial Model ')
    .replace(/\bStage\s*10\s*(Entrepreneur(\s*Readiness)?|Readiness)?:?\s*/gi, (m) => m.includes(':') ? 'Entrepreneur Readiness: ' : 'Entrepreneur Readiness ')
    .replace(/\bStage\s*11\s*(Risk(\s*Resilience|\s*Assessment|\s*Engine)?)?:?\s*/gi, (m) => m.includes(':') ? 'Enterprise Risk Engine: ' : 'Enterprise Risk Engine ')
    .replace(/\bStage\s*12\s*(Feasibility(\s*Engine)?)?:?\s*/gi, (m) => m.includes(':') ? 'Feasibility Engine: ' : 'Feasibility Engine ')
    .replace(/\bStage\s*13\s*(Dynamic\s*SWOT|SWOT)?:?\s*/gi, (m) => m.includes(':') ? 'SWOT Analysis: ' : 'SWOT Analysis ')
    .replace(/\bStage\s*14\s*(Bank\s*DPR|DPR)?:?\s*/gi, (m) => m.includes(':') ? 'DPR Generation: ' : 'DPR Generation ')
    .replace(/\bStage\s*15\s*(Personal\s*AI\s*Business\s*Assistant|Business\s*Advisor|Personal\s*Business\s*Advisor|Advisor)?:?\s*/gi, (m) => m.includes(':') ? 'KALPA AI Advisor: ' : 'KALPA AI Advisor ')
    .replace(/\bStage\s*3\s*(Business\s*Profile|Profile)?:?\s*/gi, (m) => m.includes(':') ? 'Business Profile: ' : 'Business Profile ')
    .replace(/\bStages?\s*(6–13|6-13|6–12|6-12|6–15|6-15)\b/gi, 'Analytical Engines')
    .replace(/\bStage\s*\d+(\s*(&|\/)\s*\d+)?\b/gi, '')
    // Clean punctuation artifacts
    .replace(/:\s*,/g, ',')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

/**
 * Safely parses inline markdown formatting (*italic*, **bold**, `code`) into React elements.
 */
function renderInlineText(text) {
  if (!text) return null;

  // Split by inline markdown tokens: bold **...**, italic *...*, code `...`
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  const parts = text.split(regex);

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-bold text-[#1C1917]">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return (
        <em key={index} className="italic text-[#28231F]">
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={index}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/20 font-mono text-xs"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

/**
 * Parses raw markdown text into structured blocks (headings, lists, tables, paragraphs).
 */
function parseMarkdownBlocks(rawText) {
  if (!rawText) return [];

  const cleanText = sanitizeAssistantText(rawText);
  const lines = cleanText.split('\n');
  const blocks = [];
  let currentList = null; // { type: 'bullet' | 'numbered', items: [] }
  let currentTable = null; // { headers: [], rows: [] }
  let currentParagraph = [];

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      const text = currentParagraph.join(' ').trim();
      if (text) {
        blocks.push({ type: 'paragraph', text });
      }
      currentParagraph = [];
    }
  };

  const flushList = () => {
    if (currentList) {
      blocks.push(currentList);
      currentList = null;
    }
  };

  const flushTable = () => {
    if (currentTable) {
      blocks.push(currentTable);
      currentTable = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const line = rawLine.trim();

    // Empty Line
    if (!line) {
      flushParagraph();
      flushList();
      flushTable();
      continue;
    }

    // Markdown Table Row (| col1 | col2 |)
    if (line.startsWith('|') && line.endsWith('|')) {
      flushParagraph();
      flushList();

      const cells = line
        .split('|')
        .slice(1, -1)
        .map((c) => c.trim());

      // Check if divider line (|---|---|)
      const isDivider = cells.every((c) => /^:?-+:?$/.test(c));

      if (isDivider) {
        continue;
      }

      if (!currentTable) {
        currentTable = { type: 'table', headers: cells, rows: [] };
      } else {
        currentTable.rows.push(cells);
      }
      continue;
    } else {
      flushTable();
    }

    // Headings: #, ##, ###, #### (with or without strict spacing)
    const headingMatch = line.match(/^(#{1,4})\s*(.+)$/);
    if (headingMatch) {
      flushParagraph();
      flushList();
      const level = headingMatch[1].length;
      const headingText = headingMatch[2].replace(/^#+\s*/, '').trim();
      blocks.push({ type: 'heading', level, text: headingText });
      continue;
    }

    // Standalone bold header pattern
    const standaloneBoldHeader = line.match(/^\*\*([^*]+)\*\*$/);
    if (standaloneBoldHeader && line.length < 80) {
      flushParagraph();
      flushList();
      blocks.push({ type: 'heading', level: 3, text: standaloneBoldHeader[1].trim() });
      continue;
    }

    // Numbered List Item: "1. item" or "1) item"
    const numberedMatch = line.match(/^(\d+)[\.\)]\s+(.+)$/);
    if (numberedMatch) {
      flushParagraph();
      const num = parseInt(numberedMatch[1], 10);
      const itemText = numberedMatch[2].trim();

      if (!currentList || currentList.type !== 'numbered') {
        flushList();
        currentList = { type: 'numbered', items: [] };
      }
      currentList.items.push({ num, text: itemText });
      continue;
    }

    // Bullet List Item: "- item", "* item", "• item"
    const bulletMatch = line.match(/^[-*•]\s+(.+)$/);
    if (bulletMatch) {
      flushParagraph();
      const itemText = bulletMatch[1].trim();

      if (!currentList || currentList.type !== 'bullet') {
        flushList();
        currentList = { type: 'bullet', items: [] };
      }
      currentList.items.push({ text: itemText });
      continue;
    }

    // Regular text line inside paragraph
    flushList();
    currentParagraph.push(line);
  }

  flushParagraph();
  flushList();
  flushTable();

  return blocks;
}

/**
 * AssistantMessageRenderer
 * Renders structured, clean advisory content in KALPA design language.
 */
export default function AssistantMessageRenderer({ content, className = '' }) {
  const blocks = useMemo(() => parseMarkdownBlocks(content), [content]);

  if (!content || !content.trim()) {
    return null;
  }

  return (
    <div className={`space-y-3.5 text-[#28231F] leading-relaxed font-sans ${className}`}>
      {blocks.map((block, idx) => {
        switch (block.type) {
          case 'heading': {
            const isTopLevel = block.level === 1 || block.level === 2;
            return (
              <div
                key={idx}
                className={`pt-2 pb-1 flex items-center gap-2 border-b border-[#79563F]/15 ${
                  isTopLevel ? 'text-[#1C1917] font-bold' : 'text-[#1C1917] font-semibold'
                }`}
              >
                <div className="w-1.5 h-3.5 rounded-full bg-[#79563F] shrink-0" />
                <h3
                  className={`tracking-tight font-['Outfit',sans-serif] ${
                    isTopLevel ? 'text-base font-bold' : 'text-sm font-semibold'
                  }`}
                >
                  {renderInlineText(block.text)}
                </h3>
              </div>
            );
          }

          case 'paragraph': {
            return (
              <p key={idx} className="text-xs sm:text-[13px] leading-relaxed text-[#28231F]">
                {renderInlineText(block.text)}
              </p>
            );
          }

          case 'numbered': {
            return (
              <div key={idx} className="space-y-2 my-2">
                {block.items.map((item, itemIdx) => (
                  <div
                    key={itemIdx}
                    className="flex items-start gap-2.5 p-2.5 rounded-xl bg-[#FAF2E3]/60 border border-[#79563F]/15 hover:bg-[#FAF2E3] transition-colors"
                  >
                    <div className="w-5 h-5 rounded-full bg-[#79563F] text-white font-bold text-[10px] flex items-center justify-center shrink-0 shadow-2xs mt-0.5">
                      {item.num || itemIdx + 1}
                    </div>
                    <div className="text-xs sm:text-[13px] text-[#28231F] leading-snug pt-0.5">
                      {renderInlineText(item.text)}
                    </div>
                  </div>
                ))}
              </div>
            );
          }

          case 'bullet': {
            return (
              <ul key={idx} className="space-y-1.5 my-1.5 pl-1">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="flex items-start gap-2 text-xs sm:text-[13px] text-[#28231F] leading-snug">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#79563F] shrink-0 mt-1.5" />
                    <div className="flex-1">{renderInlineText(item.text)}</div>
                  </li>
                ))}
              </ul>
            );
          }

          case 'table': {
            return (
              <div key={idx} className="my-3 overflow-x-auto rounded-xl border border-[#79563F]/20 shadow-2xs">
                <table className="min-w-full divide-y divide-[#79563F]/15 text-xs text-left">
                  <thead className="bg-[#FAF2E3] text-[#1C1917] font-bold uppercase tracking-wider">
                    <tr>
                      {block.headers.map((header, hIdx) => (
                        <th key={hIdx} className="px-3 py-2 border-r border-[#79563F]/15 last:border-r-0">
                          {renderInlineText(header)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#79563F]/10 bg-white">
                    {block.rows.map((row, rIdx) => (
                      <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-[#FAF7F2]'}>
                        {row.map((cell, cIdx) => (
                          <td
                            key={cIdx}
                            className="px-3 py-2 text-[#28231F] border-r border-[#79563F]/10 last:border-r-0 whitespace-nowrap"
                          >
                            {renderInlineText(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }

          default:
            return null;
        }
      })}
    </div>
  );
}
