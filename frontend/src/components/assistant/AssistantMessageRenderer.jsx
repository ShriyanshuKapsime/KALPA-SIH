import React, { useMemo } from 'react';
import { CheckCircle2, ChevronRight, AlertCircle, Info, Sparkles, Table as TableIcon } from 'lucide-react';

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
        <strong key={index} className="font-bold text-stone-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return (
        <em key={index} className="italic text-stone-800">
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={index}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-stone-100 text-amber-900 border border-stone-200 font-mono text-xs"
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

  const lines = rawText.split('\n');
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
        // Just divider, ignore
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

    // Headings: #, ##, ###, #### or standalone uppercase header like "WHY THIS MATTERS" or "**What you should do**"
    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      flushList();
      const level = headingMatch[1].length;
      const headingText = headingMatch[2].trim();
      blocks.push({ type: 'heading', level, text: headingText });
      continue;
    }

    // Standalone bold header pattern: e.g. "**Why this matters**" or "**1. Direct Answer**"
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
 * Renders structured, beautiful advisory content with visual hierarchy,
 * badges, cards, tables, and typography tailored for rural Bharat entrepreneurship.
 */
export default function AssistantMessageRenderer({ content, className = '' }) {
  const blocks = useMemo(() => parseMarkdownBlocks(content), [content]);

  if (!content || !content.trim()) {
    return null;
  }

  return (
    <div className={`space-y-3.5 text-stone-800 leading-relaxed font-['Inter',sans-serif] ${className}`}>
      {blocks.map((block, idx) => {
        switch (block.type) {
          case 'heading': {
            const isTopLevel = block.level === 1 || block.level === 2;
            return (
              <div
                key={idx}
                className={`pt-2.5 pb-1 flex items-center gap-2 border-b border-stone-200/80 ${
                  isTopLevel ? 'text-amber-950 font-bold' : 'text-stone-900 font-semibold'
                }`}
              >
                <div className="w-1.5 h-4 rounded-full bg-amber-600 shrink-0" />
                <h3
                  className={`tracking-tight font-['Outfit',sans-serif] ${
                    isTopLevel ? 'text-base sm:text-lg font-bold' : 'text-sm sm:text-base font-semibold'
                  }`}
                >
                  {renderInlineText(block.text)}
                </h3>
              </div>
            );
          }

          case 'paragraph': {
            return (
              <p key={idx} className="text-sm leading-6 text-stone-800">
                {renderInlineText(block.text)}
              </p>
            );
          }

          case 'numbered': {
            return (
              <div key={idx} className="space-y-2.5 my-2">
                {block.items.map((item, itemIdx) => (
                  <div
                    key={itemIdx}
                    className="flex items-start gap-3 p-2.5 rounded-xl bg-amber-50/50 border border-amber-200/50 hover:bg-amber-50 transition-colors"
                  >
                    <div className="w-6 h-6 rounded-full bg-amber-600 text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                      {item.num || itemIdx + 1}
                    </div>
                    <div className="text-sm text-stone-800 leading-snug pt-0.5">
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
                  <li key={itemIdx} className="flex items-start gap-2.5 text-sm text-stone-800 leading-snug">
                    <div className="w-1.5 h-1.5 rounded-full bg-amber-700 shrink-0 mt-2" />
                    <div className="flex-1">{renderInlineText(item.text)}</div>
                  </li>
                ))}
              </ul>
            );
          }

          case 'table': {
            return (
              <div key={idx} className="my-3 overflow-x-auto rounded-xl border border-stone-200 shadow-sm">
                <table className="min-w-full divide-y divide-stone-200 text-xs text-left">
                  <thead className="bg-stone-100 text-stone-700 font-semibold uppercase tracking-wider">
                    <tr>
                      {block.headers.map((header, hIdx) => (
                        <th key={hIdx} className="px-3 py-2 border-r border-stone-200 last:border-r-0">
                          {renderInlineText(header)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100 bg-white">
                    {block.rows.map((row, rIdx) => (
                      <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-stone-50/60'}>
                        {row.map((cell, cIdx) => (
                          <td
                            key={cIdx}
                            className="px-3 py-2 text-stone-800 border-r border-stone-100 last:border-r-0 whitespace-nowrap"
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
