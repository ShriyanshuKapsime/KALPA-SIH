import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { SUPPORTED_LANGUAGES, TRANSLATIONS } from '../i18n/translations';
import apiService from '../services/api';

const LanguageContext = createContext(null);

const STORAGE_KEY = 'kalpa_universal_language';
const DYNAMIC_CACHE_KEY = 'kalpa_dynamic_translation_cache_v2';

// In-memory fast cache for dynamic translation: key = `${srcLang}:${tgtLang}:${text}`
export const inMemoryTranslationCache = new Map();

// Reverse lookup map: translatedText -> originalEnglishText
export const reverseTranslationMap = new Map();

// Load initial persistent cache from sessionStorage/localStorage
try {
  const cached = sessionStorage.getItem(DYNAMIC_CACHE_KEY);
  if (cached) {
    const parsed = JSON.parse(cached);
    Object.entries(parsed).forEach(([k, v]) => inMemoryTranslationCache.set(k, v));
  }
} catch (e) {
  console.warn('[LanguageContext] Cache initialization warning:', e);
}

// Prepopulate cache and reverse map from static translations dictionary for instant sub-millisecond lookups
try {
  SUPPORTED_LANGUAGES.forEach((lang) => {
    if (lang.code === 'en') return;
    const dict = TRANSLATIONS[lang.code] || {};
    const enDict = TRANSLATIONS.en || {};
    Object.entries(enDict).forEach(([key, enText]) => {
      const targetText = dict[key];
      if (enText && targetText && typeof enText === 'string' && typeof targetText === 'string') {
        const enClean = enText.trim();
        const tgtClean = targetText.trim();
        const cacheKey = `en:${lang.code}:${enClean}`;
        if (!inMemoryTranslationCache.has(cacheKey)) {
          inMemoryTranslationCache.set(cacheKey, tgtClean);
        }
        reverseTranslationMap.set(tgtClean, enClean);
      }
    });
  });
} catch (e) {}

export const saveDynamicCache = () => {
  try {
    const obj = {};
    let count = 0;
    for (const [k, v] of inMemoryTranslationCache.entries()) {
      if (count++ > 2000) break; // Store up to 2000 frequent translations
      obj[k] = v;
    }
    sessionStorage.setItem(DYNAMIC_CACHE_KEY, JSON.stringify(obj));
  } catch (e) {}
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguageState] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) || sessionStorage.getItem('kalpa_selected_language');
      if (stored && SUPPORTED_LANGUAGES.some((l) => l.code === stored)) {
        return stored;
      }
    } catch (e) {
      console.warn('[LanguageContext] Storage read error:', e);
    }
    return 'en'; // Default to English
  });

  const [isTranslatingPage, setIsTranslatingPage] = useState(false);

  const setLanguage = useCallback((newLang) => {
    if (!newLang || !SUPPORTED_LANGUAGES.some((l) => l.code === newLang)) return;
    setLanguageState(newLang);
    try {
      localStorage.setItem(STORAGE_KEY, newLang);
      sessionStorage.setItem('kalpa_selected_language', newLang);
      sessionStorage.setItem('kalpa_assistant_language', newLang);
      // Dispatch a custom event so the global page translator and non-react listeners can react immediately
      window.dispatchEvent(new CustomEvent('kalpa-language-change', { detail: { language: newLang } }));
    } catch (e) {
      console.warn('[LanguageContext] Storage write error:', e);
    }
  }, []);

  // Sync with storage events from other tabs
  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === STORAGE_KEY && e.newValue && SUPPORTED_LANGUAGES.some((l) => l.code === e.newValue)) {
        setLanguageState(e.newValue);
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  // Static Dictionary translation helper function
  const t = useCallback(
    (key, fallback) => {
      if (!key) return '';
      const dict = TRANSLATIONS[language] || TRANSLATIONS.en || {};
      if (dict[key] !== undefined) {
        return dict[key];
      }
      const enDict = TRANSLATIONS.en || {};
      if (enDict[key] !== undefined) {
        return enDict[key];
      }
      return fallback !== undefined ? fallback : key;
    },
    [language]
  );

  // Dynamic text translation helper with instant caching
  const translateDynamic = useCallback(
    async (text, targetLang = language, sourceLang = 'en') => {
      if (!text || typeof text !== 'string' || !text.trim()) return text || '';
      if (targetLang === 'en' || targetLang === sourceLang) return text;

      const cleanText = text.trim();
      const cacheKey = `${sourceLang}:${targetLang}:${cleanText}`;
      if (inMemoryTranslationCache.has(cacheKey)) {
        return inMemoryTranslationCache.get(cacheKey);
      }

      // Check if text exists in static dictionary
      const staticKey = Object.keys(TRANSLATIONS.en || {}).find(
        (k) => TRANSLATIONS.en[k] && TRANSLATIONS.en[k].toLowerCase() === cleanText.toLowerCase()
      );
      if (staticKey && TRANSLATIONS[targetLang] && TRANSLATIONS[targetLang][staticKey]) {
        const trans = TRANSLATIONS[targetLang][staticKey];
        inMemoryTranslationCache.set(cacheKey, trans);
        return trans;
      }

      try {
        const res = await apiService.translate.text(cleanText, targetLang, sourceLang);
        if (res?.translated_text) {
          inMemoryTranslationCache.set(cacheKey, res.translated_text);
          reverseTranslationMap.set(res.translated_text.trim(), cleanText);
          saveDynamicCache();
          return res.translated_text;
        }
      } catch (err) {
        console.warn('[LanguageContext] Dynamic translate error:', err);
      }

      return text;
    },
    [language]
  );

  // Batch text translation helper with deduplication and caching
  const translateBatch = useCallback(
    async (texts, targetLang = language, sourceLang = 'en') => {
      if (!texts || !Array.isArray(texts) || texts.length === 0) return [];
      if (targetLang === 'en' || targetLang === sourceLang) return texts;

      const uncachedIndices = [];
      const uncachedTexts = [];
      const results = new Array(texts.length);

      texts.forEach((txt, idx) => {
        if (!txt || typeof txt !== 'string' || !txt.trim()) {
          results[idx] = txt || '';
          return;
        }
        const clean = txt.trim();
        const cacheKey = `${sourceLang}:${targetLang}:${clean}`;

        if (inMemoryTranslationCache.has(cacheKey)) {
          results[idx] = inMemoryTranslationCache.get(cacheKey);
        } else {
          // Check static dictionary
          const staticKey = Object.keys(TRANSLATIONS.en || {}).find(
            (k) => TRANSLATIONS.en[k] && TRANSLATIONS.en[k].toLowerCase() === clean.toLowerCase()
          );
          if (staticKey && TRANSLATIONS[targetLang] && TRANSLATIONS[targetLang][staticKey]) {
            const trans = TRANSLATIONS[targetLang][staticKey];
            inMemoryTranslationCache.set(cacheKey, trans);
            reverseTranslationMap.set(trans.trim(), clean);
            results[idx] = trans;
          } else {
            uncachedIndices.push(idx);
            uncachedTexts.push(clean);
          }
        }
      });

      if (uncachedTexts.length > 0) {
        try {
          // Batch into chunks of up to 40 strings
          const CHUNK_SIZE = 40;
          for (let i = 0; i < uncachedTexts.length; i += CHUNK_SIZE) {
            const chunkTexts = uncachedTexts.slice(i, i + CHUNK_SIZE);
            const chunkIndices = uncachedIndices.slice(i, i + CHUNK_SIZE);

            const res = await apiService.translate.batch(chunkTexts, targetLang, sourceLang);
            const translatedArray = res?.translated_texts || [];

            chunkTexts.forEach((original, cIdx) => {
              const translated = translatedArray[cIdx] || original;
              const originalIndex = chunkIndices[cIdx];
              results[originalIndex] = translated;
              inMemoryTranslationCache.set(`${sourceLang}:${targetLang}:${original}`, translated);
              if (translated && translated.trim()) {
                reverseTranslationMap.set(translated.trim(), original.trim());
              }
            });
          }
          saveDynamicCache();
        } catch (err) {
          console.warn('[LanguageContext] Batch translation error:', err);
          uncachedIndices.forEach((origIdx, cIdx) => {
            if (results[origIdx] === undefined) {
              results[origIdx] = uncachedTexts[cIdx];
            }
          });
        }
      }

      // Fill any remaining undefined
      for (let i = 0; i < results.length; i++) {
        if (results[i] === undefined) results[i] = texts[i];
      }

      return results;
    },
    [language]
  );

  // Dynamic JSON object translation helper
  const translateDynamicObject = useCallback(
    async (data, targetLang = language, sourceLang = 'en') => {
      if (!data) return data;
      if (targetLang === 'en' || targetLang === sourceLang) return data;

      try {
        const res = await apiService.translate.object(data, targetLang, sourceLang);
        if (res?.data) {
          return res.data;
        }
      } catch (err) {
        console.warn('[LanguageContext] Dynamic object translate error:', err);
      }
      return data;
    },
    [language]
  );

  const currentLanguageInfo = useMemo(() => {
    return SUPPORTED_LANGUAGES.find((l) => l.code === language) || SUPPORTED_LANGUAGES[0];
  }, [language]);

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t,
      translateDynamic,
      translateBatch,
      translateDynamicObject,
      availableLanguages: SUPPORTED_LANGUAGES,
      currentLanguageInfo,
      isTranslatingPage,
      setIsTranslatingPage,
    }),
    [language, setLanguage, t, translateDynamic, translateBatch, translateDynamicObject, currentLanguageInfo, isTranslatingPage]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    return {
      language: 'en',
      setLanguage: () => {},
      t: (key, fallback) => (TRANSLATIONS.en && TRANSLATIONS.en[key]) || fallback || key,
      translateDynamic: async (text) => text,
      translateBatch: async (texts) => texts,
      translateDynamicObject: async (obj) => obj,
      availableLanguages: SUPPORTED_LANGUAGES,
      currentLanguageInfo: SUPPORTED_LANGUAGES[0],
      isTranslatingPage: false,
      setIsTranslatingPage: () => {},
    };
  }
  return context;
};

/**
 * React hook to automatically translate a dynamic string when language changes.
 */
export const useAutoTranslate = (text, defaultFallback = '') => {
  const { language, translateDynamic } = useLanguage();
  const [translated, setTranslated] = useState(text || defaultFallback);
  const [isTranslating, setIsTranslating] = useState(false);

  useEffect(() => {
    let isMounted = true;
    if (!text || typeof text !== 'string') {
      setTranslated(text || defaultFallback);
      return;
    }

    if (language === 'en') {
      setTranslated(text);
      return;
    }

    const run = async () => {
      setIsTranslating(true);
      try {
        const result = await translateDynamic(text, language);
        if (isMounted) {
          setTranslated(result);
        }
      } catch (e) {
        if (isMounted) setTranslated(text);
      } finally {
        if (isMounted) setIsTranslating(false);
      }
    };

    run();
    return () => {
      isMounted = false;
    };
  }, [text, language, translateDynamic, defaultFallback]);

  return { translatedText: translated, isTranslating };
};

/**
 * Component to wrap dynamic text and render it translated in the active language.
 */
export const TranslatedText = ({ text, fallback = '' }) => {
  const { translatedText } = useAutoTranslate(text, fallback);
  return <>{translatedText || text || fallback}</>;
};

export default LanguageContext;
