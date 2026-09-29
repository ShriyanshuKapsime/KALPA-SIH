import React, { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useLanguage, reverseTranslationMap, inMemoryTranslationCache } from '../../context/LanguageContext';

// WeakMaps to permanently store canonical original English text and attributes for every DOM node
const canonicalTextWeakMap = new WeakMap();
const canonicalAttrWeakMap = new WeakMap();

// Tags that should never be translated or mutated
const EXCLUDED_TAGS = new Set([
  'SCRIPT',
  'STYLE',
  'NOSCRIPT',
  'SVG',
  'PATH',
  'CODE',
  'PRE',
  'TEXTAREA',
]);

/**
 * Checks if a string contains translatable natural language text.
 */
function isTranslatableText(text) {
  if (!text || typeof text !== 'string') return false;
  const trimmed = text.trim();
  if (!trimmed) return false;

  // Ignore URLs, file paths, endpoints
  if (
    trimmed.startsWith('http://') ||
    trimmed.startsWith('https://') ||
    trimmed.startsWith('/api/') ||
    trimmed.startsWith('file:///')
  ) {
    return false;
  }

  // Ignore UUIDs and hashes
  if (/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(trimmed)) {
    return false;
  }

  // Ignore pure numbers, currency, ratios, percentages (e.g. "₹4,50,000", "24.5%", "1.25x")
  const stripped = trimmed
    .replace(/[₹$,%xX/\\:;+\-()\[\]{}·|~@#*]/g, '')
    .replace(/\s+/g, '')
    .trim();
  if (!stripped || /^\d+(\.\d+)?$/.test(stripped)) {
    return false;
  }

  // Ignore technical date formats
  if (/^\d{4}-\d{2}-\d{2}/.test(trimmed) || /^\d{1,2}:\d{2}(\s*(AM|PM))?$/i.test(trimmed)) {
    return false;
  }

  return true;
}

/**
 * Checks if an element or any ancestor should be excluded from translation.
 */
function isExcludedElement(element) {
  if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;
  let curr = element;
  while (curr && curr !== document.body) {
    if (EXCLUDED_TAGS.has(curr.tagName)) return true;
    if (curr.hasAttribute && (curr.hasAttribute('data-no-translate') || curr.getAttribute('translate') === 'no')) {
      return true;
    }
    if (curr.classList && curr.classList.contains('no-translate')) {
      return true;
    }
    curr = curr.parentElement;
  }
  return false;
}

export const GlobalPageTranslator = () => {
  const { language, translateBatch, setIsTranslatingPage } = useLanguage();
  const location = useLocation();
  const isApplyingRef = useRef(false);
  const epochRef = useRef(0);
  const debounceTimerRef = useRef(null);
  const currentLangRef = useRef(language);

  currentLangRef.current = language;

  /**
   * 1. RESTORE CANONICAL ENGLISH (Synchronous, 0ms latency, zero reload)
   * Walks the full DOM and restores every node directly from its canonical source text.
   */
  const restoreCanonicalEnglish = () => {
    isApplyingRef.current = true;
    try {
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: (node) => {
            if (!node.parentElement) return NodeFilter.FILTER_REJECT;
            if (isExcludedElement(node.parentElement)) return NodeFilter.FILTER_REJECT;
            return NodeFilter.FILTER_ACCEPT;
          },
        },
        false
      );

      let node;
      while ((node = walker.nextNode())) {
        // Retrieve canonical English source
        let canonical = node.__kalpa_canonical || canonicalTextWeakMap.get(node);
        if (!canonical) {
          const val = node.nodeValue?.trim();
          if (val && reverseTranslationMap && reverseTranslationMap.has(val)) {
            canonical = reverseTranslationMap.get(val);
          }
        }

        if (canonical) {
          // Restore canonical English text
          const origVal = node.nodeValue || '';
          const leadingWs = origVal.match(/^\s*/)?.[0] || '';
          const trailingWs = origVal.match(/\s*$/)?.[0] || '';
          const expected = leadingWs + canonical + trailingWs;
          if (node.nodeValue !== expected) {
            node.nodeValue = expected;
          }
          node.__kalpa_canonical = canonical;
          canonicalTextWeakMap.set(node, canonical);
          node.__kalpa_lang = 'en';
        }
      }

      // Revert user-facing attributes
      const elementsWithAttrs = document.querySelectorAll('input[placeholder], textarea[placeholder], button[aria-label], [title]');
      elementsWithAttrs.forEach((el) => {
        if (isExcludedElement(el)) return;
        const origAttrs = el.__kalpa_canonical_attrs || canonicalAttrWeakMap.get(el);
        if (origAttrs) {
          Object.entries(origAttrs).forEach(([attr, val]) => {
            el.setAttribute(attr, val);
          });
          el.__kalpa_attr_lang = 'en';
        } else if (reverseTranslationMap) {
          ['placeholder', 'aria-label', 'title'].forEach((attr) => {
            if (el.hasAttribute(attr)) {
              const currVal = el.getAttribute(attr)?.trim();
              if (currVal && reverseTranslationMap.has(currVal)) {
                el.setAttribute(attr, reverseTranslationMap.get(currVal));
              }
            }
          });
          el.__kalpa_attr_lang = 'en';
        }
      });
    } catch (e) {
      console.warn('[GlobalPageTranslator] Error restoring English:', e);
    } finally {
      isApplyingRef.current = false;
      setIsTranslatingPage(false);
    }
  };

  /**
   * 2. TRANSLATE FROM CANONICAL ENGLISH TO TARGET LANGUAGE
   * Always derives target language directly from canonical English.
   */
  const translatePageToLanguage = async (targetLang) => {
    if (targetLang === 'en') {
      restoreCanonicalEnglish();
      return;
    }

    if (isApplyingRef.current) return;

    const currentEpoch = ++epochRef.current;

    try {
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: (node) => {
            if (!node.parentElement) return NodeFilter.FILTER_REJECT;
            if (isExcludedElement(node.parentElement)) return NodeFilter.FILTER_REJECT;
            return NodeFilter.FILTER_ACCEPT;
          },
        },
        false
      );

      const textNodesToTranslate = [];
      const uniqueStringsToFetch = new Set();
      const instantTranslationLookup = new Map();

      let node;
      while ((node = walker.nextNode())) {
        let canonical = node.__kalpa_canonical || canonicalTextWeakMap.get(node);

        if (!canonical) {
          const rawVal = node.nodeValue;
          if (!rawVal || !rawVal.trim()) continue;
          const trimmed = rawVal.trim();

          // Check if this text is an existing translated string in reverse map
          if (reverseTranslationMap && reverseTranslationMap.has(trimmed)) {
            canonical = reverseTranslationMap.get(trimmed);
          } else if (isTranslatableText(trimmed)) {
            // New canonical English string
            canonical = trimmed;
          }

          if (canonical) {
            node.__kalpa_canonical = canonical;
            canonicalTextWeakMap.set(node, canonical);
          }
        }

        if (canonical && isTranslatableText(canonical)) {
          if (node.__kalpa_lang !== targetLang) {
            textNodesToTranslate.push(node);

            // Check if translation is already in fast memory cache
            const cacheKey = `en:${targetLang}:${canonical}`;
            if (inMemoryTranslationCache && inMemoryTranslationCache.has(cacheKey)) {
              instantTranslationLookup.set(canonical, inMemoryTranslationCache.get(cacheKey));
            } else {
              uniqueStringsToFetch.add(canonical);
            }
          }
        }
      }

      // Scan attributes
      const attrElementsToTranslate = [];
      const attributeElements = document.querySelectorAll('input[placeholder], textarea[placeholder], button[aria-label], [title]');
      attributeElements.forEach((el) => {
        if (isExcludedElement(el)) return;

        let origAttrs = el.__kalpa_canonical_attrs || canonicalAttrWeakMap.get(el);
        if (!origAttrs) {
          origAttrs = {};
          if (el.hasAttribute('placeholder')) origAttrs.placeholder = el.getAttribute('placeholder');
          if (el.hasAttribute('aria-label')) origAttrs['aria-label'] = el.getAttribute('aria-label');
          if (el.hasAttribute('title')) origAttrs.title = el.getAttribute('title');
          el.__kalpa_canonical_attrs = origAttrs;
          canonicalAttrWeakMap.set(el, origAttrs);
        }

        if (el.__kalpa_attr_lang !== targetLang) {
          Object.entries(origAttrs).forEach(([attrName, canonicalVal]) => {
            if (canonicalVal && isTranslatableText(canonicalVal)) {
              attrElementsToTranslate.push({ element: el, attribute: attrName, canonical: canonicalVal });
              const cacheKey = `en:${targetLang}:${canonicalVal.trim()}`;
              if (inMemoryTranslationCache && inMemoryTranslationCache.has(cacheKey)) {
                instantTranslationLookup.set(canonicalVal.trim(), inMemoryTranslationCache.get(cacheKey));
              } else {
                uniqueStringsToFetch.add(canonicalVal.trim());
              }
            }
          });
        }
      });

      // Apply any instantly available cached translations first (0ms)
      if (instantTranslationLookup.size > 0) {
        isApplyingRef.current = true;
        textNodesToTranslate.forEach((tNode) => {
          const canonical = tNode.__kalpa_canonical;
          if (canonical && instantTranslationLookup.has(canonical)) {
            const trans = instantTranslationLookup.get(canonical);
            const origVal = tNode.nodeValue || '';
            const leadingWs = origVal.match(/^\s*/)?.[0] || '';
            const trailingWs = origVal.match(/\s*$/)?.[0] || '';
            tNode.nodeValue = leadingWs + trans + trailingWs;
            tNode.__kalpa_lang = targetLang;
          }
        });

        attrElementsToTranslate.forEach(({ element, attribute, canonical }) => {
          const trimmed = canonical.trim();
          if (instantTranslationLookup.has(trimmed)) {
            element.setAttribute(attribute, instantTranslationLookup.get(trimmed));
            element.__kalpa_attr_lang = targetLang;
          }
        });
        isApplyingRef.current = false;
      }

      // If no remaining uncached strings, complete immediately
      if (uniqueStringsToFetch.size === 0) {
        setIsTranslatingPage(false);
        return;
      }

      setIsTranslatingPage(true);

      const uniqueStringsArray = Array.from(uniqueStringsToFetch);
      const translatedArray = await translateBatch(uniqueStringsArray, targetLang, 'en');

      // CRITICAL CHECK: Invariant guard — If user switched to English or another language during network await, abort!
      if (epochRef.current !== currentEpoch || currentLangRef.current !== targetLang) {
        if (currentLangRef.current === 'en') {
          restoreCanonicalEnglish();
        }
        return;
      }

      // Build complete translation lookup map from response
      const translationLookup = new Map(instantTranslationLookup);
      uniqueStringsArray.forEach((canonical, idx) => {
        const trans = translatedArray[idx] || canonical;
        translationLookup.set(canonical, trans);
      });

      // Apply newly fetched translations safely to DOM
      isApplyingRef.current = true;

      textNodesToTranslate.forEach((tNode) => {
        const canonical = tNode.__kalpa_canonical;
        if (canonical && translationLookup.has(canonical)) {
          const trans = translationLookup.get(canonical);
          if (trans && trans !== canonical) {
            const origVal = tNode.nodeValue || '';
            const leadingWs = origVal.match(/^\s*/)?.[0] || '';
            const trailingWs = origVal.match(/\s*$/)?.[0] || '';
            tNode.nodeValue = leadingWs + trans + trailingWs;
          }
          tNode.__kalpa_lang = targetLang;
        }
      });

      attrElementsToTranslate.forEach(({ element, attribute, canonical }) => {
        const trimmed = canonical.trim();
        if (translationLookup.has(trimmed)) {
          element.setAttribute(attribute, translationLookup.get(trimmed));
          element.__kalpa_attr_lang = targetLang;
        }
      });
    } catch (err) {
      console.warn('[GlobalPageTranslator] Translation error:', err);
    } finally {
      isApplyingRef.current = false;
      setIsTranslatingPage(false);
    }
  };

  const scheduleTranslation = () => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(() => {
      translatePageToLanguage(currentLangRef.current);
    }, 60);
  };

  // 1. React language state listener
  useEffect(() => {
    currentLangRef.current = language;
    epochRef.current += 1;
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    if (language === 'en') {
      restoreCanonicalEnglish();
    } else {
      scheduleTranslation();
    }
  }, [language]);

  // 2. Custom event listener for instant multi-component / navbar sync
  useEffect(() => {
    const handleLanguageChangeEvent = (e) => {
      const newLang = e.detail?.language;
      if (newLang) {
        currentLangRef.current = newLang;
        epochRef.current += 1;
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }
        if (newLang === 'en') {
          restoreCanonicalEnglish();
        } else {
          scheduleTranslation();
        }
      }
    };
    window.addEventListener('kalpa-language-change', handleLanguageChangeEvent);
    return () => window.removeEventListener('kalpa-language-change', handleLanguageChangeEvent);
  }, []);

  // 3. Route change effect
  useEffect(() => {
    if (language !== 'en') {
      scheduleTranslation();
    }
  }, [location.pathname, location.search]);

  // 4. MutationObserver for dynamically added nodes
  useEffect(() => {
    const observer = new MutationObserver((mutations) => {
      if (isApplyingRef.current) return;

      let hasRelevantChange = false;
      for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          for (const node of mutation.addedNodes) {
            if (node.nodeType === Node.ELEMENT_NODE && !isExcludedElement(node)) {
              hasRelevantChange = true;
              break;
            } else if (node.nodeType === Node.TEXT_NODE && isTranslatableText(node.nodeValue)) {
              hasRelevantChange = true;
              break;
            }
          }
        }
        if (hasRelevantChange) break;
      }

      if (hasRelevantChange) {
        if (currentLangRef.current !== 'en') {
          scheduleTranslation();
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    return () => {
      observer.disconnect();
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return null; // Headless component
};

export default GlobalPageTranslator;
