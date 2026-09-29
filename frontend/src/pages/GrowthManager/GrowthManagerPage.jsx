import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Lightbulb,
  Wallet,
  Package,
  Truck,
  Receipt,
  TrendingUp,
  Store,
  ShoppingCart,
  MessageCircle,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  ArrowLeft,
  Plus,
  Camera,
  Mic,
  MicOff,
  Edit3,
  Trash2,
  Eye,
  Check,
  X,
  RefreshCw,
  MapPin,
  Building2,
  ShieldCheck,
  ChevronRight,
  Search,
  Filter,
  Activity,
  Send,
  Sliders,
  Globe,
  Bell,
  Settings,
  Menu,
  Star,
  Users,
  Tag,
  DollarSign,
  PieChart,
  Layers,
} from 'lucide-react';
import apiService from '../../services/api';
import LanguageSelector from '../../components/ui/LanguageSelector';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';

export const GrowthManagerPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const {
    businessName: ctxBusinessName,
    businessId: ctxBusinessId,
    sessionId: ctxSessionId,
  } = useWorkflow();
  const { language, t } = useLanguage();

  const businessId = (
    searchParams.get('business_id') ||
    ctxBusinessId ||
    sessionStorage.getItem('kalpa_business_id') ||
    'business'
  ).trim();

  const activeSessionId = (
    searchParams.get('session_id') ||
    ctxSessionId ||
    sessionStorage.getItem('kalpa_session_id') ||
    ''
  ).trim();

  const scenarioId = (
    searchParams.get('scenario_id') ||
    sessionStorage.getItem(`kalpa_dpr_scenario_${businessId}`) ||
    'default'
  ).trim();

  // Active business name resolution
  const [businessName, setBusinessName] = useState(() => {
    return (
      sessionStorage.getItem('kalpa_business_name') ||
      ctxBusinessName ||
      'Kamadhenu Dairy & Milk Production'
    );
  });

  const [businessCategory, setBusinessCategory] = useState('Commercial Dairy Farm & Milk Production');
  const [contextData, setContextData] = useState(null);
  const [loadingContext, setLoadingContext] = useState(false);

  // Active Sidebar View State: 'health' (default) | 'recommendations' | 'cashflow' | 'inventory' | 'supplychain' | 'expenses' | 'demand' | 'selling' | 'orders' | 'growth' | 'assistant' | 'storefront'
  const [activeView, setActiveView] = useState('health');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Storefront Internal Tab State
  const [storefrontTab, setStorefrontTab] = useState('overview'); // 'overview' | 'products' | 'inventory' | 'orders' | 'customers' | 'reviews' | 'offers' | 'settings' | 'advisor'

  // Business Assistant State (Drawer + Dedicated View)
  const [assistantDrawerOpen, setAssistantDrawerOpen] = useState(false);
  const [assistantMessages, setAssistantMessages] = useState([
    {
      role: 'assistant',
      text: `Namaste! I am your KALPA Business Operating Assistant for **${businessName}**. How can I help you operate, optimize cash flow, or grow your business today?`,
    },
  ]);
  const [assistantInput, setAssistantInput] = useState('');
  const [assistantLoading, setAssistantLoading] = useState(false);
  const assistantScrollRef = useRef(null);

  // Notifications State
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'warning',
      title: 'Upcoming Loan EMI in 8 Days',
      message: 'Monthly EMI of ₹18,450 is scheduled for auto-debit. Current cash balance is sufficient (10x coverage).',
      time: 'Today',
      read: false,
    },
    {
      id: 2,
      type: 'info',
      title: 'Supply Chain Delay Detected',
      message: 'Cattle feed consignment from Sri Sai Agri Commodities delayed by 2 days due to highway transport.',
      time: '1h ago',
      read: false,
    },
    {
      id: 3,
      type: 'success',
      title: 'Local Demand Surge Detected',
      message: 'Morning retail milk delivery inquiries in your 1.5 km radius are +18% higher.',
      time: '3h ago',
      read: false,
    },
  ]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Load canonical context from DPR/Gateway on mount
  useEffect(() => {
    if (businessId && businessId !== 'business') {
      setLoadingContext(true);
      apiService.dpr
        .getContext(businessId, { scenario_id: scenarioId })
        .then((res) => {
          const data = res?.data || res;
          if (data) {
            setContextData(data);
            const bName =
              data.business_profile?.enterprise_name ||
              data.business_profile?.business_name ||
              data.fields?.enterprise_name?.value;
            if (bName && !sessionStorage.getItem('kalpa_business_name')) {
              setBusinessName(bName);
            }
            const bCat =
              data.business_profile?.category ||
              data.business_profile?.industry_type ||
              data.fields?.business_activity?.value;
            if (bCat) {
              setBusinessCategory(bCat);
            }
          }
        })
        .catch((err) => {
          console.warn('[GrowthManagerPage] Context fetch warning:', err);
        })
        .finally(() => {
          setLoadingContext(false);
        });
    }
  }, [businessId, scenarioId]);

  // Pre-calculated deterministic metrics from DPR or robust fallbacks
  const financialMetrics = useMemo(() => {
    const finPkg = contextData?.financial_package || {};
    const bm = finPkg.banking_metrics || {};
    const fields = contextData?.fields || {};

    const totalProjectCost =
      finPkg.total_project_cost ||
      fields.total_project_cost?.value ||
      fields.glance_total_project_cost?.value ||
      1250000;

    const termLoan =
      finPkg.term_loan ||
      fields.bank_term_loan_amount?.value ||
      fields.glance_term_loan?.value ||
      937500;

    const interestRate = 0.085; // 8.5% p.a.
    const tenureMonths = 60; // 5 years
    const monthlyRate = interestRate / 12;
    const emi = Math.round(
      (termLoan * monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) /
        (Math.pow(1 + monthlyRate, tenureMonths) - 1)
    );

    return {
      totalProjectCost,
      termLoan,
      emi: emi || 18450,
      dscr: bm.average_dscr || fields.glance_average_dscr?.value || 1.82,
      promoterMargin: totalProjectCost - termLoan,
    };
  }, [contextData]);

  // -------------------------------------------------------------
  // AGENT RECOMMENDATIONS (AWAITING APPROVAL)
  // -------------------------------------------------------------
  const [recommendations, setRecommendations] = useState([
    {
      id: 'REC-01',
      category: 'Payments',
      title: 'SUPPLIER PAYMENT',
      subtitle: 'Payment due to Village Milk Federation',
      detection: 'Weekly raw milk procurement invoice verified against weighbridge receipts.',
      whyMatters: 'Preserves 100% vendor trust and guarantees uninterrupted morning inflow.',
      recommendation: 'Schedule payment before tomorrow’s bank cutoff.',
      amount: '₹18,500',
      timing: 'Due tomorrow',
      status: 'Awaiting approval',
      approved: false,
    },
    {
      id: 'REC-02',
      category: 'Inventory',
      title: 'REORDER CATTLE FEED',
      subtitle: 'Feed stock threshold reached (12 bags remaining)',
      detection: 'Consumption rate is 1.2 bags/day. Current stock covers 3.5 days.',
      whyMatters: 'Prevents nutritional gaps that impact morning herd milk yield.',
      recommendation: 'Place purchase order for 15 bags with Sri Sai Agri Commodities.',
      amount: '₹21,750 (15 Bags)',
      timing: 'Action recommended today',
      status: 'Awaiting approval',
      approved: false,
    },
    {
      id: 'REC-03',
      category: 'Demand & Expansion',
      title: 'RETAIL ROUTE EXPANSION',
      subtitle: '12 new household delivery requests detected in Sector 4',
      detection: 'Local morning demand rising +18% in 1.5 km delivery radius.',
      whyMatters: 'Direct retail margins are 33.7% vs 18% wholesale.',
      recommendation: 'Activate Sector 4 morning delivery slot (6:15 AM - 7:00 AM).',
      amount: '+₹16,200/mo projected revenue',
      timing: 'Route optimization',
      status: 'Awaiting approval',
      approved: false,
    },
  ]);

  const handleApproveRecommendation = (recId) => {
    setRecommendations((prev) =>
      prev.map((r) =>
        r.id === recId ? { ...r, status: 'Approved & Executing', approved: true } : r
      )
    );
  };

  const handleReviewRecommendation = (rec) => {
    setAssistantDrawerOpen(true);
    handleAssistantSend(`Please provide a detailed financial and operational review for: ${rec.title} (${rec.amount}). What are the risks, cash impact, and alternative actions?`);
  };

  // -------------------------------------------------------------
  // INVENTORY MODULE STATE
  // -------------------------------------------------------------
  const [inventory, setInventory] = useState([
    {
      id: 'INV-001',
      name: 'Fresh Cow Milk (Pasteurized)',
      sku: 'MILK-500ML',
      category: 'Dairy Products',
      unit: 'Litres',
      quantity: 145,
      reorderLevel: 50,
      purchaseCost: 42,
      sellingPrice: 56,
      supplier: 'Village Dairy Co-op Federation',
      status: 'In Stock',
      ordersCount: 84,
    },
    {
      id: 'INV-002',
      name: 'Traditional Cultured Ghee (A2)',
      sku: 'GHEE-1KG',
      category: 'Processed Dairy',
      unit: 'Kg',
      quantity: 32,
      reorderLevel: 15,
      purchaseCost: 480,
      sellingPrice: 720,
      supplier: 'Internal Farm Processing',
      status: 'In Stock',
      ordersCount: 26,
    },
    {
      id: 'INV-003',
      name: 'Fresh Artisanal Paneer',
      sku: 'PAN-200G',
      category: 'Fresh Cheese',
      unit: 'Kg',
      quantity: 18,
      reorderLevel: 20,
      purchaseCost: 260,
      sellingPrice: 380,
      supplier: 'Internal Processing Unit',
      status: 'Low Stock',
      ordersCount: 39,
    },
    {
      id: 'INV-004',
      name: 'Enriched Cattle Feed Mash',
      sku: 'FEED-50KG',
      category: 'Raw Materials',
      unit: 'Bags',
      quantity: 12,
      reorderLevel: 15,
      purchaseCost: 1450,
      sellingPrice: 1650,
      supplier: 'Sri Sai Agri Commodities',
      status: 'Reorder Soon',
      ordersCount: 8,
    },
  ]);

  const [addProductModalOpen, setAddProductModalOpen] = useState(false);
  const [draftProduct, setDraftProduct] = useState({
    name: '',
    sku: '',
    category: 'Dairy Products',
    unit: 'Units',
    quantity: 10,
    reorderLevel: 5,
    purchaseCost: 50,
    sellingPrice: 75,
    supplier: 'Local Supplier',
  });
  const [photoUploading, setPhotoUploading] = useState(false);
  const [voiceRecording, setVoiceRecording] = useState(false);
  const [showReviewConfirm, setShowReviewConfirm] = useState(false);

  const handlePhotoAdd = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPhotoUploading(true);
    setTimeout(() => {
      setPhotoUploading(false);
      setDraftProduct({
        name: 'Organic Buffalo Curd (Dahi)',
        sku: 'CURD-500G',
        category: 'Dairy Products',
        unit: 'Pots',
        quantity: 40,
        reorderLevel: 10,
        purchaseCost: 35,
        sellingPrice: 50,
        supplier: 'Kamadhenu Processing',
      });
      setShowReviewConfirm(true);
    }, 900);
  };

  const handleVoiceAddToggle = () => {
    if (voiceRecording) {
      setVoiceRecording(false);
      setDraftProduct({
        name: 'Fresh Cow Milk (Morning Batch)',
        sku: 'MILK-MOR-20L',
        category: 'Dairy Products',
        unit: 'Litres',
        quantity: 20,
        reorderLevel: 5,
        purchaseCost: 40,
        sellingPrice: 55,
        supplier: 'Local Herds',
      });
      setShowReviewConfirm(true);
    } else {
      setVoiceRecording(true);
    }
  };

  const handleConfirmAddProduct = () => {
    const newId = `INV-${String(inventory.length + 1).padStart(3, '0')}`;
    setInventory((prev) => [
      ...prev,
      {
        ...draftProduct,
        id: newId,
        quantity: Number(draftProduct.quantity) || 1,
        purchaseCost: Number(draftProduct.purchaseCost) || 0,
        sellingPrice: Number(draftProduct.sellingPrice) || 0,
        reorderLevel: Number(draftProduct.reorderLevel) || 5,
        status: Number(draftProduct.quantity) <= Number(draftProduct.reorderLevel) ? 'Low Stock' : 'In Stock',
        ordersCount: 0,
      },
    ]);
    setAddProductModalOpen(false);
    setShowReviewConfirm(false);
    setDraftProduct({
      name: '',
      sku: '',
      category: 'Dairy Products',
      unit: 'Units',
      quantity: 10,
      reorderLevel: 5,
      purchaseCost: 50,
      sellingPrice: 75,
      supplier: 'Local Supplier',
    });
  };

  // -------------------------------------------------------------
  // SUPPLY CHAIN & TRANSACTIONS STATE
  // -------------------------------------------------------------
  const [suppliers] = useState([
    {
      id: 'SUP-01',
      name: 'Village Dairy Co-op Federation',
      category: 'Raw Milk Inflow',
      unitPrice: '₹42 / Litre',
      volume: '150 L/day',
      paymentStatus: 'Paid (Weekly)',
      deliveryStatus: 'On Time (Daily 6 AM)',
      reliability: '96%',
      nextDelivery: 'Tomorrow, 6:00 AM',
    },
    {
      id: 'SUP-02',
      name: 'Sri Sai Agri Commodities',
      category: 'Cattle Feed & Mineral Mix',
      unitPrice: '₹1,450 / Bag',
      volume: '15 Bags/mo',
      paymentStatus: 'Due in 3 Days (₹21,750)',
      deliveryStatus: 'Delayed by 2 Days',
      reliability: '68%',
      nextDelivery: 'Wednesday, 2:00 PM',
    },
    {
      id: 'SUP-03',
      name: 'Bharat Packaging Solutions',
      category: 'Pouches & Glass Bottles',
      unitPrice: '₹2.80 / Pouch',
      volume: '3,000 Units',
      paymentStatus: 'Paid',
      deliveryStatus: 'Delivered',
      reliability: '92%',
      nextDelivery: '15 Oct 2026',
    },
  ]);

  const [cashTransactions, setCashTransactions] = useState([
    { id: 'TX-101', date: '28 Sep 2026', type: 'Inflow', category: 'Retail Sales', description: 'Daily retail counter milk & curd sales', amount: 8450 },
    { id: 'TX-102', date: '27 Sep 2026', type: 'Inflow', category: 'B2B Wholesale', description: 'Weekly supply to Hotel Shanti Sagar', amount: 24600 },
    { id: 'TX-103', date: '26 Sep 2026', type: 'Outflow', category: 'Raw Materials', description: 'Weekly payment to Village Milk Federation', amount: 35280 },
    { id: 'TX-104', date: '25 Sep 2026', type: 'Outflow', category: 'Utilities', description: 'Monthly chilling unit electricity bill', amount: 4850 },
    { id: 'TX-105', date: '24 Sep 2026', type: 'Outflow', category: 'Transport', description: 'Morning collection route fuel & vehicle maintenance', amount: 1600 },
  ]);

  const [transactionModalOpen, setTransactionModalOpen] = useState(false);
  const [draftTransaction, setDraftTransaction] = useState({
    date: new Date().toISOString().split('T')[0],
    type: 'Outflow',
    category: 'Utilities',
    description: '',
    amount: '',
  });

  const handleAddTransaction = () => {
    if (!draftTransaction.amount || !draftTransaction.description) return;
    setCashTransactions((prev) => [
      {
        id: `TX-${prev.length + 101}`,
        date: draftTransaction.date,
        type: draftTransaction.type,
        category: draftTransaction.category,
        description: draftTransaction.description,
        amount: Number(draftTransaction.amount),
      },
      ...prev,
    ]);
    setTransactionModalOpen(false);
    setDraftTransaction({
      date: new Date().toISOString().split('T')[0],
      type: 'Outflow',
      category: 'Utilities',
      description: '',
      amount: '',
    });
  };

  // -------------------------------------------------------------
  // ORDERS & STOREFRONT STATE
  // -------------------------------------------------------------
  const [storeOrders, setStoreOrders] = useState([
    {
      id: 'ORD-901',
      customer: 'Priya Sharma',
      locality: 'Sector 4 (1.2 km away)',
      phone: '+91 98451 22345',
      items: '2L Fresh Milk + 500g Curd',
      amount: 162,
      status: 'New',
      time: '12 mins ago',
      deliverySlot: 'Today, 6:00 PM',
    },
    {
      id: 'ORD-902',
      customer: 'Hotel Green Leaf',
      locality: 'Station Road (2.8 km away)',
      phone: '+91 94481 99120',
      items: '15L Morning Milk + 2kg Paneer',
      amount: 1600,
      status: 'Accepted',
      time: '45 mins ago',
      deliverySlot: 'Tomorrow, 6:30 AM',
    },
    {
      id: 'ORD-903',
      customer: 'Rajesh Patil',
      locality: 'Gandhi Nagar (0.8 km away)',
      phone: '+91 97312 44589',
      items: '1kg Pure Ghee (A2)',
      amount: 720,
      status: 'Dispatched',
      time: '2 hours ago',
      deliverySlot: 'Out for delivery',
    },
  ]);

  const handleUpdateOrderStatus = (orderId, newStatus) => {
    setStoreOrders((prev) =>
      prev.map((o) => (o.id === orderId ? { ...o, status: newStatus } : o))
    );
  };

  const [storeCustomers] = useState([
    { id: 'CUST-01', name: 'Priya Sharma', locality: 'Sector 4', ordersCount: 14, totalSpent: 2280, phone: '+91 98451 22345' },
    { id: 'CUST-02', name: 'Hotel Green Leaf (Mgr: Anand)', locality: 'Station Road', ordersCount: 32, totalSpent: 48600, phone: '+91 94481 99120' },
    { id: 'CUST-03', name: 'Rajesh Patil', locality: 'Gandhi Nagar', ordersCount: 8, totalSpent: 5760, phone: '+91 97312 44589' },
    { id: 'CUST-04', name: 'Sunita Joshi', locality: 'Housing Colony', ordersCount: 19, totalSpent: 3120, phone: '+91 99002 33411' },
  ]);

  const [storeReviews] = useState([
    { id: 'REV-01', customer: 'Priya Sharma', rating: 5, date: '27 Sep 2026', comment: 'Milk quality is very pure and thick. Delivery on time every evening.' },
    { id: 'REV-02', customer: 'Rajesh Patil', rating: 5, date: '25 Sep 2026', comment: 'A2 Ghee aroma is authentic like traditional village bilona ghee.' },
    { id: 'REV-03', customer: 'Sunita Joshi', rating: 4, date: '22 Sep 2026', comment: 'Paneer is extremely fresh, but morning delivery arrived around 7:15 AM. Prefer before 6:30 AM.' },
  ]);

  const [storeOffers, setStoreOffers] = useState([
    { id: 'OFF-01', name: 'Morning Milk Subscription Bundle', discount: '5% off on monthly advance', code: 'MORNING5', active: true },
    { id: 'OFF-02', name: 'Festive A2 Ghee Combo (2kg)', discount: '₹100 flat discount', code: 'FESTIVEGHEE', active: true },
  ]);

  const [createOfferModalOpen, setCreateOfferModalOpen] = useState(false);
  const [draftOffer, setDraftOffer] = useState({ name: '', discount: '', code: '' });

  const handleAddOffer = () => {
    if (!draftOffer.name || !draftOffer.discount) return;
    setStoreOffers((prev) => [
      ...prev,
      {
        id: `OFF-0${prev.length + 1}`,
        name: draftOffer.name,
        discount: draftOffer.discount,
        code: (draftOffer.code || draftOffer.name.slice(0, 6)).toUpperCase(),
        active: true,
      },
    ]);
    setCreateOfferModalOpen(false);
    setDraftOffer({ name: '', discount: '', code: '' });
  };

  // -------------------------------------------------------------
  // ASSISTANT SEND HANDLER
  // -------------------------------------------------------------
  const handleAssistantSend = async (customPrompt = null) => {
    const messageToSend = (customPrompt || assistantInput).trim();
    if (!messageToSend || assistantLoading) return;

    const userMsg = { role: 'user', text: messageToSend };
    setAssistantMessages((prev) => [...prev, userMsg]);
    setAssistantInput('');
    setAssistantLoading(true);

    setTimeout(() => {
      if (assistantScrollRef.current) {
        assistantScrollRef.current.scrollTop = assistantScrollRef.current.scrollHeight;
      }
    }, 100);

    try {
      const response = await apiService.assistant.chat(
        {
          message: messageToSend,
          conversation_history: assistantMessages.slice(-6).map((m) => ({
            role: m.role,
            content: m.text,
          })),
          language: language || 'en',
          context_override: {
            business_name: businessName,
            total_project_cost: financialMetrics.totalProjectCost,
            bank_term_loan: financialMetrics.termLoan,
            monthly_emi: financialMetrics.emi,
            dscr: financialMetrics.dscr,
            inventory_items_count: inventory.length,
            cash_balance: 185400,
            active_suppliers: suppliers.map((s) => s.name).join(', '),
          },
        },
        businessId
      );

      const aiReply =
        response?.reply ||
        response?.data?.reply ||
        response?.message ||
        `Based on your cash position of ₹1,85,400, monthly EMI of ₹${financialMetrics.emi.toLocaleString('en-IN')}, and 33.7% operating margin: your working capital buffer is sound. KALPA recommends settling the feed supplier payment tomorrow while fulfilling morning delivery routes.`;

      setAssistantMessages((prev) => [...prev, { role: 'assistant', text: aiReply }]);
    } catch (err) {
      console.warn('[GrowthManager] Assistant response fallback:', err);
      setAssistantMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Operational review for **${businessName}**:\n\n• **Cash Runway**: ₹1,85,400 (Healthy 34-day buffer)\n• **Upcoming EMI**: ₹${financialMetrics.emi.toLocaleString('en-IN')} (Due in 8 days · 10x coverage)\n• **Inventory Health**: 4 SKUs tracked with 2 low-stock alerts\n• **Recommendation**: Approve feed reorder to maintain milk production volume.`,
        },
      ]);
    } finally {
      setAssistantLoading(false);
      setTimeout(() => {
        if (assistantScrollRef.current) {
          assistantScrollRef.current.scrollTop = assistantScrollRef.current.scrollHeight;
        }
      }, 100);
    }
  };

  const totalInventoryValue = inventory.reduce(
    (acc, item) => acc + item.quantity * item.purchaseCost,
    0
  );

  const pendingRecommendationsCount = recommendations.filter((r) => !r.approved).length;
  const pendingOrdersCount = storeOrders.filter((o) => o.status === 'New' || o.status === 'Accepted').length;

  // Sidebar navigation structure
  const navigationSections = [
    {
      title: 'OVERVIEW',
      items: [
        { id: 'health', label: 'Business Health', icon: LayoutDashboard },
        { id: 'recommendations', label: 'Recommendations', icon: Lightbulb, badge: pendingRecommendationsCount },
      ],
    },
    {
      title: 'OPERATIONS',
      items: [
        { id: 'cashflow', label: 'Cash Flow', icon: Wallet },
        { id: 'inventory', label: 'Inventory', icon: Package, badge: inventory.filter(i => i.status !== 'In Stock').length },
        { id: 'supplychain', label: 'Supply Chain', icon: Truck },
        { id: 'expenses', label: 'Expenses', icon: Receipt },
        { id: 'demand', label: 'Demand Monitor', icon: TrendingUp },
      ],
    },
    {
      title: 'SELLING',
      items: [
        { id: 'selling', label: 'Online Selling', icon: Store },
        { id: 'orders', label: 'Orders', icon: ShoppingCart, badge: pendingOrdersCount },
      ],
    },
    {
      title: 'GROWTH',
      items: [
        { id: 'growth', label: 'Growth Advisor', icon: TrendingUp },
      ],
    },
    {
      title: 'ASSISTANCE',
      items: [
        { id: 'assistant', label: 'Ask KALPA', icon: MessageCircle },
      ],
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6 space-y-4 animate-fadeIn pb-20 text-[#1C1917]">
      {/* Top Portal Title */}
      <div className="text-center space-y-1 pt-1 pb-1">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-[#1B4D3E] font-['Playfair_Display',Georgia,serif]">
          KALPA GROWTH MANAGER
        </h1>
        <p className="text-xs sm:text-sm font-semibold tracking-wider uppercase text-[#79563F]">
          Post-launch Business Operating Portal
        </p>
      </div>

      {/* ============================================================
          1. PERSISTENT BUSINESS CONTEXT & PORTAL HEADER
          ============================================================ */}
      <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-4 sm:p-5 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Left: Brand + Dynamic Business Identity */}
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-1.5 rounded-xl bg-white border border-[#79563F]/25 text-[#79563F] cursor-pointer"
                title="Toggle Navigation Menu"
              >
                <Menu className="w-4 h-4" />
              </button>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#1B4D3E] text-white tracking-wider uppercase shadow-2xs">
                KALPA Growth Manager
              </span>
              <span className="text-[11px] text-[#79563F]/60">·</span>
              <span className="text-[11px] font-semibold text-[#1B4D3E] flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#1B4D3E]" />
                Active
              </span>
            </div>

            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold text-[#1C1917] font-['Outfit']">
                {businessName}
              </h1>
              <button
                type="button"
                onClick={() => {
                  const newName = prompt('Update Enterprise Name:', businessName);
                  if (newName && newName.trim()) {
                    setBusinessName(newName.trim());
                    sessionStorage.setItem('kalpa_business_name', newName.trim());
                  }
                }}
                className="p-1 rounded-lg hover:bg-white/60 text-[#79563F] transition cursor-pointer"
                title="Edit Business Name"
              >
                <Edit3 className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs text-[#79563F] font-medium">
              {businessCategory}
            </p>
          </div>

          {/* Right Controls: Quick Actions */}
          <div className="flex items-center flex-wrap gap-2.5 self-start md:self-center">
            {/* Ask KALPA Drawer Launcher */}
            <button
              type="button"
              onClick={() => setAssistantDrawerOpen(true)}
              className="saffron-gradient-btn px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs cursor-pointer transition-all hover:scale-[1.02]"
            >
              <MessageCircle className="w-3.5 h-3.5" />
              <span>Ask KALPA</span>
            </button>

            {/* Notifications */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowNotifications((prev) => !prev)}
                className="p-2 rounded-xl bg-white hover:bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 shadow-2xs relative cursor-pointer"
                title="Notifications"
              >
                <Bell className="w-4 h-4" />
                {notifications.some((n) => !n.read) && (
                  <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#C86D3B]" />
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 rounded-2xl bg-[#FAF7F2] border border-[#79563F]/25 shadow-xl p-3 z-50 animate-fadeIn space-y-2">
                  <div className="flex items-center justify-between pb-1.5 border-b border-[#79563F]/15">
                    <span className="text-xs font-bold text-[#1C1917]">Operating Signals</span>
                    <button
                      type="button"
                      onClick={() => setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))}
                      className="text-[10px] text-[#79563F] hover:underline cursor-pointer"
                    >
                      Mark all read
                    </button>
                  </div>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`p-2.5 rounded-xl text-xs border ${
                          n.type === 'warning'
                            ? 'bg-amber-50 border-amber-200 text-amber-900'
                            : n.type === 'success'
                            ? 'bg-[#EAF5EE] border-[#1B4D3E]/30 text-[#1B4D3E]'
                            : 'bg-white border-[#79563F]/20 text-[#79563F]'
                        }`}
                      >
                        <div className="font-bold flex items-center justify-between">
                          <span>{n.title}</span>
                          <span className="text-[10px] opacity-75">{n.time}</span>
                        </div>
                        <p className="text-[11px] mt-0.5 leading-relaxed">{n.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Business Settings */}
            <button
              type="button"
              onClick={() => setShowSettingsModal(true)}
              className="p-2 rounded-xl bg-white hover:bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 shadow-2xs cursor-pointer"
              title="Business Settings"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* Language Selector */}
            <LanguageSelector compact />
          </div>
        </div>
      </div>

      {/* ============================================================
          2. MAIN SIDEBAR + CONTENT SPLIT LAYOUT
          ============================================================ */}
      <div className="flex flex-col lg:flex-row gap-5 items-start">
        {/* ============================================================
            A. LEFT SIDEBAR NAVIGATION (Desktop: 230px, Mobile: Drawer)
            ============================================================ */}
        <aside
          className={`lg:w-60 w-full shrink-0 bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-3.5 space-y-4 shadow-2xs ${
            mobileMenuOpen ? 'block' : 'hidden lg:block'
          }`}
        >
          {navigationSections.map((sec, sIdx) => (
            <div key={sIdx} className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F]/80 px-2.5 block">
                {sec.title}
              </span>
              <div className="space-y-0.5">
                {sec.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeView === item.id;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        setActiveView(item.id);
                        setMobileMenuOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        isActive
                          ? 'bg-[#79563F] text-white shadow-2xs'
                          : 'text-[#79563F] hover:bg-white/70 hover:text-[#1C1917]'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className="w-4 h-4 shrink-0" />
                        <span>{item.label}</span>
                      </div>
                      {typeof item.badge === 'number' && item.badge > 0 && (
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
                            isActive
                              ? 'bg-white text-[#79563F]'
                              : 'bg-[#C86D3B] text-white'
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Quick Storefront Direct Shortcut */}
          <div className="pt-2 border-t border-[#79563F]/15">
            <button
              type="button"
              onClick={() => {
                setActiveView('storefront');
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                activeView === 'storefront'
                  ? 'bg-[#1B4D3E] text-white shadow-2xs'
                  : 'bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30 hover:bg-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <Store className="w-4 h-4 shrink-0" />
                <span>KALPA Storefront</span>
              </div>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </aside>

        {/* ============================================================
            B. MAIN CONTENT OPERATING WORKSPACE
            ============================================================ */}
        <main className="flex-1 w-full min-w-0 space-y-4">
          {/* ==========================================================
              VIEW 1: BUSINESS HEALTH / OVERVIEW (DEFAULT LANDING VIEW)
              Compact above-the-fold workspace answering:
              1. Is my business healthy?
              2. What is happening? (Live Monitor)
              3. What does KALPA recommend? (Top 2-3 Actions)
              4. Does KALPA need my approval?
              ========================================================== */}
          {activeView === 'health' && (
            <div className="space-y-4 animate-fadeIn">
              {/* 1. Core Health Metrics (6 Cards) */}
              <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-4 sm:p-5 shadow-2xs space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-[#79563F] flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5" />
                    <span>Business Health Overview</span>
                  </h2>
                  <span className="text-[11px] font-semibold text-[#1B4D3E] bg-[#EAF5EE] px-2.5 py-0.5 rounded-md border border-[#1B4D3E]/30">
                    All Core Systems Healthy
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
                  <div className="bg-[#FAF7F2] p-3 rounded-2xl border border-[#79563F]/15">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Cash Position</span>
                    <span className="text-base sm:text-lg font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">₹1,85,400</span>
                    <span className="text-[10px] text-[#1B4D3E] font-semibold">▲ +12.4% this mo</span>
                  </div>

                  <div className="bg-[#FAF7F2] p-3 rounded-2xl border border-[#79563F]/15">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Monthly Revenue</span>
                    <span className="text-base sm:text-lg font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">₹2,45,000</span>
                    <span className="text-[10px] text-[#79563F]">Target: ₹3,00,000</span>
                  </div>

                  <div className="bg-[#FAF7F2] p-3 rounded-2xl border border-[#79563F]/15">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Monthly Expenses</span>
                    <span className="text-base sm:text-lg font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">₹1,62,500</span>
                    <span className="text-[10px] text-[#79563F]">OpEx &amp; Feed</span>
                  </div>

                  <div className="bg-[#FAF7F2] p-3 rounded-2xl border border-[#79563F]/15">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Gross Margin</span>
                    <span className="text-base sm:text-lg font-bold text-[#1B4D3E] font-['Outfit'] block mt-0.5">33.7%</span>
                    <span className="text-[10px] text-[#1B4D3E] font-semibold">Healthy unit margin</span>
                  </div>

                  <div className="bg-[#FAF7F2] p-3 rounded-2xl border border-[#79563F]/15">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Upcoming EMI</span>
                    <span className="text-base sm:text-lg font-bold text-[#C86D3B] font-['Outfit'] block mt-0.5">
                      ₹{financialMetrics.emi.toLocaleString('en-IN')}
                    </span>
                    <span className="text-[10px] text-[#C86D3B] font-semibold">Due in 8 days</span>
                  </div>

                  <div className="bg-[#FAF7F2] p-3 rounded-2xl border border-[#79563F]/15">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Inventory Value</span>
                    <span className="text-base sm:text-lg font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">
                      ₹{totalInventoryValue.toLocaleString('en-IN')}
                    </span>
                    <span className="text-[10px] text-[#79563F]">{inventory.length} active SKUs</span>
                  </div>
                </div>
              </div>

              {/* 2. KALPA MONITOR (Live Signals Strip) */}
              <div className="bg-[#FAF7F2] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs space-y-2">
                <div className="flex items-center justify-between pb-1 border-b border-[#79563F]/15">
                  <div className="flex items-center gap-1.5">
                    <Activity className="w-4 h-4 text-[#1B4D3E]" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917]">
                      KALPA MONITOR
                    </h3>
                  </div>
                  <span className="text-[11px] text-[#79563F] italic">
                    Watching cash, inventory, demand and upcoming obligations
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 text-xs">
                  <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-[#79563F]/15">
                    <span className="w-2 h-2 rounded-full bg-[#1B4D3E] shrink-0" />
                    <span className="text-[#1C1917] font-medium truncate">Cash position healthy (₹1,85,400 available buffer)</span>
                  </div>

                  <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-[#79563F]/15">
                    <span className="w-2 h-2 rounded-full bg-[#C86D3B] shrink-0" />
                    <span className="text-[#1C1917] font-medium truncate">EMI due in 8 days (₹18,450 auto-debit scheduled)</span>
                  </div>

                  <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-[#79563F]/15">
                    <span className="w-2 h-2 rounded-full bg-amber-600 shrink-0" />
                    <span className="text-[#1C1917] font-medium truncate">Fresh milk stock below preferred level</span>
                  </div>

                  <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-[#79563F]/15">
                    <span className="w-2 h-2 rounded-full bg-[#1B4D3E] shrink-0" />
                    <span className="text-[#1C1917] font-medium truncate">Local demand increasing (+18% morning inquiries)</span>
                  </div>

                  <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-[#79563F]/15">
                    <span className="w-2 h-2 rounded-full bg-[#C86D3B] shrink-0" />
                    <span className="text-[#1C1917] font-medium truncate">Supplier payment awaiting approval (₹18,500)</span>
                  </div>

                  <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-[#79563F]/15">
                    <span className="w-2 h-2 rounded-full bg-[#1B4D3E] shrink-0" />
                    <span className="text-[#1C1917] font-medium truncate">Storefront operational with 3 active orders</span>
                  </div>
                </div>
              </div>

              {/* 3. RECOMMENDATIONS (AWAITING YOUR APPROVAL) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between px-1">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-1.5">
                      <Lightbulb className="w-4 h-4 text-[#C86D3B]" />
                      <span>RECOMMENDATIONS · Awaiting your approval</span>
                    </h3>
                    <p className="text-[11px] text-[#79563F]">
                      Nothing executes without your explicit authorization.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setActiveView('recommendations')}
                    className="text-xs font-bold text-[#79563F] hover:text-[#1C1917] hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <span>View all ({recommendations.length})</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="space-y-2.5">
                  {recommendations.slice(0, 2).map((rec) => (
                    <div
                      key={rec.id}
                      className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-2xl p-4 shadow-2xs space-y-2.5 hover:border-[#79563F]/40 transition-all"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-bold px-2.5 py-0.5 rounded-md uppercase tracking-wider border ${
                              rec.approved
                                ? 'bg-[#EAF5EE] border-[#1B4D3E]/30 text-[#1B4D3E]'
                                : 'bg-[#FDF4EE] border-[#C86D3B]/30 text-[#C86D3B]'
                            }`}
                          >
                            {rec.approved ? 'Approved & Executing' : 'Awaiting Approval'}
                          </span>
                          <span className="text-xs font-bold text-[#1C1917]">{rec.title}</span>
                        </div>
                        <span className="text-xs font-semibold text-[#79563F]">{rec.timing}</span>
                      </div>

                      <div className="text-xs space-y-1">
                        <p className="text-[#1C1917] font-semibold">{rec.subtitle}</p>
                        <p className="text-[#79563F] leading-relaxed">{rec.detection}</p>
                        <div className="p-2.5 rounded-xl bg-white border border-[#79563F]/15 flex items-center justify-between gap-3">
                          <span className="text-xs text-[#1C1917] font-medium">{rec.recommendation}</span>
                          <span className="text-xs font-bold text-[#1B4D3E] font-['Outfit'] shrink-0">{rec.amount}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-end gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => handleReviewRecommendation(rec)}
                          className="px-3 py-1.5 rounded-xl bg-white hover:bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/30 text-xs font-bold transition cursor-pointer"
                        >
                          Review
                        </button>
                        <button
                          type="button"
                          disabled={rec.approved}
                          onClick={() => handleApproveRecommendation(rec.id)}
                          className={`px-4 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
                            rec.approved
                              ? 'bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30 cursor-default'
                              : 'saffron-gradient-btn shadow-2xs cursor-pointer hover:scale-[1.02]'
                          }`}
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>{rec.approved ? 'Approved' : 'Approve'}</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 2: ALL RECOMMENDATIONS
              ========================================================== */}
          {activeView === 'recommendations' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="pb-3 border-b border-[#79563F]/15 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-[#C86D3B]" />
                    <span>All Operating Recommendations</span>
                  </h3>
                  <p className="text-xs text-[#79563F] mt-0.5">
                    Proactive interventions generated by KALPA’s continuous telemetry.
                  </p>
                </div>
                <span className="text-xs font-bold text-[#79563F]">
                  {pendingRecommendationsCount} Awaiting Authorization
                </span>
              </div>

              <div className="space-y-3">
                {recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className="bg-white border border-[#79563F]/20 rounded-2xl p-4 sm:p-5 shadow-2xs space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold px-2.5 py-0.5 rounded-md uppercase tracking-wider border ${
                            rec.approved
                              ? 'bg-[#EAF5EE] border-[#1B4D3E]/30 text-[#1B4D3E]'
                              : 'bg-[#FDF4EE] border-[#C86D3B]/30 text-[#C86D3B]'
                          }`}
                        >
                          {rec.approved ? 'Approved & Executing' : 'Awaiting Approval'}
                        </span>
                        <span className="text-xs font-bold text-[#1C1917]">{rec.title}</span>
                      </div>
                      <span className="text-xs font-semibold text-[#79563F]">{rec.timing}</span>
                    </div>

                    <div className="text-xs space-y-1.5">
                      <p className="text-sm font-bold text-[#1C1917]">{rec.subtitle}</p>
                      <p className="text-[#79563F] leading-relaxed"><strong className="text-[#1C1917]">Signal:</strong> {rec.detection}</p>
                      <p className="text-[#79563F] leading-relaxed"><strong className="text-[#1C1917]">Impact:</strong> {rec.whyMatters}</p>
                      <div className="p-3 rounded-xl bg-[#FAF7F2] border border-[#79563F]/15 flex items-center justify-between gap-3">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F] block">Proposed Action</span>
                          <span className="text-xs text-[#1C1917] font-semibold">{rec.recommendation}</span>
                        </div>
                        <span className="text-sm font-bold text-[#1B4D3E] font-['Outfit']">{rec.amount}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-2.5 pt-1">
                      <button
                        type="button"
                        onClick={() => handleReviewRecommendation(rec)}
                        className="px-3.5 py-1.5 rounded-xl bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/30 text-xs font-bold cursor-pointer"
                      >
                        Review Analysis
                      </button>
                      <button
                        type="button"
                        disabled={rec.approved}
                        onClick={() => handleApproveRecommendation(rec.id)}
                        className={`px-4 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
                          rec.approved
                            ? 'bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30 cursor-default'
                            : 'saffron-gradient-btn shadow-2xs cursor-pointer hover:scale-[1.02]'
                        }`}
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>{rec.approved ? 'Approved' : 'Authorize Action'}</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 3: CASH FLOW & OBLIGATIONS
              ========================================================== */}
          {activeView === 'cashflow' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#79563F]/15">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                    <Wallet className="w-4 h-4 text-[#1B4D3E]" />
                    <span>Cash Flow &amp; Debt Service</span>
                  </h3>
                  <p className="text-xs text-[#79563F] mt-0.5">
                    Real-time liquidity, buffer runway, and institutional loan repayments.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setTransactionModalOpen(true)}
                  className="saffron-gradient-btn px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs cursor-pointer self-start sm:self-center"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Record Transaction</span>
                </button>
              </div>

              {/* Cash Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                <div className="bg-[#FAF7F2] p-4 rounded-2xl border border-[#79563F]/15 space-y-1">
                  <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Available Cash Buffer</span>
                  <div className="text-xl font-bold text-[#1C1917] font-['Outfit']">₹1,85,400</div>
                  <p className="text-[11px] text-[#1B4D3E] font-medium">34 days operational coverage runway</p>
                </div>

                <div className="bg-[#FAF7F2] p-4 rounded-2xl border border-[#79563F]/15 space-y-1">
                  <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Bank Term Loan EMI</span>
                  <div className="text-xl font-bold text-[#C86D3B] font-['Outfit']">
                    ₹{financialMetrics.emi.toLocaleString('en-IN')}
                  </div>
                  <p className="text-[11px] text-[#79563F]">Auto-debit on 5th · 10x cash coverage</p>
                </div>

                <div className="bg-[#FAF7F2] p-4 rounded-2xl border border-[#79563F]/15 space-y-1">
                  <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Average DSCR</span>
                  <div className="text-xl font-bold text-[#1B4D3E] font-['Outfit']">
                    {Number(financialMetrics.dscr).toFixed(2)}x
                  </div>
                  <p className="text-[11px] text-[#1B4D3E] font-medium">Viable for bank debt service (&gt;= 1.5x)</p>
                </div>
              </div>

              {/* Recent Transactions Table */}
              <div className="space-y-2 pt-2">
                <span className="text-xs font-bold text-[#1C1917] block">Operating Cash Transactions</span>
                <div className="space-y-2">
                  {cashTransactions.map((tx) => (
                    <div
                      key={tx.id}
                      className="flex items-center justify-between p-3 rounded-xl bg-white border border-[#79563F]/15 text-xs gap-3"
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span className={`w-2 h-2 rounded-full shrink-0 ${
                          tx.type === 'Inflow' ? 'bg-[#1B4D3E]' : 'bg-[#79563F]'
                        }`} />
                        <div className="min-w-0">
                          <span className="font-bold text-[#1C1917] block truncate">{tx.description}</span>
                          <span className="text-[10px] text-[#79563F]">{tx.category} · {tx.date}</span>
                        </div>
                      </div>
                      <span className={`font-bold font-['Outfit'] text-xs sm:text-sm shrink-0 ${
                        tx.type === 'Inflow' ? 'text-[#1B4D3E]' : 'text-[#1C1917]'
                      }`}>
                        {tx.type === 'Inflow' ? '+' : '-'}₹{tx.amount.toLocaleString('en-IN')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 4: INVENTORY
              ========================================================== */}
          {activeView === 'inventory' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#79563F]/15">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                    <Package className="w-4 h-4 text-[#79563F]" />
                    <span>Inventory &amp; Stock Tracking</span>
                  </h3>
                  <p className="text-xs text-[#79563F] mt-0.5">
                    Track raw materials, farm supplies, and packaged finished goods.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setAddProductModalOpen(true)}
                  className="saffron-gradient-btn px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs cursor-pointer self-start sm:self-center"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Product</span>
                </button>
              </div>

              {/* Product Inventory Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {inventory.map((item) => (
                  <div
                    key={item.id}
                    className="bg-white p-4 rounded-2xl border border-[#79563F]/15 space-y-2 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-1">
                        <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider">{item.category}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                          item.status === 'In Stock'
                            ? 'bg-[#EAF5EE] border-[#1B4D3E]/30 text-[#1B4D3E]'
                            : 'bg-amber-50 border-amber-300 text-amber-900'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                      <h5 className="font-bold text-xs sm:text-sm text-[#1C1917] mt-1">{item.name}</h5>
                      <p className="text-[11px] text-[#79563F] mt-0.5">SKU: {item.sku}</p>
                    </div>

                    <div className="pt-2 border-t border-[#79563F]/10 space-y-1 text-xs">
                      <div className="flex justify-between text-[#79563F]">
                        <span>Available Stock:</span>
                        <span className="font-bold text-[#1C1917]">{item.quantity} {item.unit}</span>
                      </div>
                      <div className="flex justify-between text-[#79563F]">
                        <span>Unit Selling Price:</span>
                        <span className="font-bold text-[#1B4D3E]">₹{item.sellingPrice}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 5: SUPPLY CHAIN
              ========================================================== */}
          {activeView === 'supplychain' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="pb-3 border-b border-[#79563F]/15">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                  <Truck className="w-4 h-4 text-[#79563F]" />
                  <span>Supply Chain &amp; Vendor Management</span>
                </h3>
                <p className="text-xs text-[#79563F] mt-0.5">
                  Vendor delivery schedules, payment statuses, and lead time reliability.
                </p>
              </div>

              <div className="space-y-3">
                {suppliers.map((sup) => (
                  <div
                    key={sup.id}
                    className="p-4 rounded-2xl bg-white border border-[#79563F]/15 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[#1C1917]">{sup.name}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30">
                          {sup.reliability} Reliability
                        </span>
                      </div>
                      <p className="text-[#79563F]">{sup.category} · Volume: {sup.volume} ({sup.unitPrice})</p>
                      <p className="text-[11px] text-[#79563F]"><strong>Delivery Status:</strong> {sup.deliveryStatus}</p>
                    </div>

                    <div className="text-left sm:text-right shrink-0 space-y-1">
                      <span className="text-[11px] font-bold text-[#79563F] block">Next Scheduled Inflow</span>
                      <span className="text-xs font-semibold text-[#1C1917] block">{sup.nextDelivery}</span>
                      <span className="text-[11px] font-semibold text-[#C86D3B]">{sup.paymentStatus}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 6: EXPENSES
              ========================================================== */}
          {activeView === 'expenses' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#79563F]/15">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                    <Receipt className="w-4 h-4 text-[#79563F]" />
                    <span>Operating Expenses (OpEx)</span>
                  </h3>
                  <p className="text-xs text-[#79563F] mt-0.5">
                    Categorized expenditure breakdown across power, logistics, feed, and maintenance.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setTransactionModalOpen(true)}
                  className="saffron-gradient-btn px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs cursor-pointer self-start sm:self-center"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Record Expense</span>
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="bg-[#FAF7F2] p-3.5 rounded-2xl border border-[#79563F]/15">
                  <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Raw Milk &amp; Feed</span>
                  <span className="text-base font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">₹1,12,500</span>
                  <span className="text-[10px] text-[#79563F]">69.2% of OpEx</span>
                </div>

                <div className="bg-[#FAF7F2] p-3.5 rounded-2xl border border-[#79563F]/15">
                  <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Utilities &amp; Power</span>
                  <span className="text-base font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">₹18,200</span>
                  <span className="text-[10px] text-[#79563F]">Chilling &amp; Storage</span>
                </div>

                <div className="bg-[#FAF7F2] p-3.5 rounded-2xl border border-[#79563F]/15">
                  <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Transport &amp; Fuel</span>
                  <span className="text-base font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">₹14,800</span>
                  <span className="text-[10px] text-[#79563F]">Morning retail runs</span>
                </div>

                <div className="bg-[#FAF7F2] p-3.5 rounded-2xl border border-[#79563F]/15">
                  <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Labour &amp; Other</span>
                  <span className="text-base font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">₹17,000</span>
                  <span className="text-[10px] text-[#79563F]">Maintenance &amp; staff</span>
                </div>
              </div>

              {/* Expense Log */}
              <div className="space-y-2 pt-2">
                <span className="text-xs font-bold text-[#1C1917] block">Recent Expense Entries</span>
                <div className="space-y-2">
                  {cashTransactions.filter(t => t.type === 'Outflow').map((tx) => (
                    <div
                      key={tx.id}
                      className="flex items-center justify-between p-3 rounded-xl bg-white border border-[#79563F]/15 text-xs"
                    >
                      <div>
                        <span className="font-bold text-[#1C1917] block">{tx.description}</span>
                        <span className="text-[10px] text-[#79563F]">{tx.category} · {tx.date}</span>
                      </div>
                      <span className="font-bold font-['Outfit'] text-xs sm:text-sm text-[#1C1917]">
                        ₹{tx.amount.toLocaleString('en-IN')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 7: DEMAND MONITOR
              ========================================================== */}
          {activeView === 'demand' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="pb-3 border-b border-[#79563F]/15">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#1B4D3E]" />
                  <span>Demand Monitor &amp; Local Market Radar</span>
                </h3>
                <p className="text-xs text-[#79563F] mt-0.5">
                  Real-time consumer demand signals, wholesale contracts, and seasonal surges.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 text-xs">
                <div className="bg-white p-4 rounded-2xl border border-[#79563F]/15 space-y-2">
                  <span className="text-[11px] font-bold text-[#1B4D3E] uppercase tracking-wider">Morning Retail Route</span>
                  <p className="font-semibold text-sm text-[#1C1917]">145 Litres/day demand</p>
                  <p className="text-[11px] text-[#79563F] leading-relaxed">
                    Peak demand window: 5:45 AM - 7:30 AM. 12 pending customer subscriptions in Sector 4.
                  </p>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-[#79563F]/15 space-y-2">
                  <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">B2B Hotel Contract</span>
                  <p className="font-semibold text-sm text-[#1C1917]">180 Litres Milk + 25kg Paneer / wk</p>
                  <p className="text-[11px] text-[#79563F] leading-relaxed">
                    Contract with Hotel Shanti Sagar stable. Weekly invoicing on Saturdays.
                  </p>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-[#79563F]/15 space-y-2">
                  <span className="text-[11px] font-bold text-[#C86D3B] uppercase tracking-wider">Festive Value-Add Surge</span>
                  <p className="font-semibold text-sm text-[#1C1917]">Ghee &amp; Butter Demand +24%</p>
                  <p className="text-[11px] text-[#79563F] leading-relaxed">
                    Higher margins on cultured A2 Ghee (@ ₹720/kg) vs raw milk sales.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 8: ONLINE SELLING (ONDC + STOREFRONT OPTION)
              ========================================================== */}
          {activeView === 'selling' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-5 animate-fadeIn">
              <div className="pb-3 border-b border-[#79563F]/15">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                  <Store className="w-4 h-4 text-[#1B4D3E]" />
                  <span>Online Selling &amp; Digital Commerce Channels</span>
                </h3>
                <p className="text-xs text-[#79563F] mt-0.5">
                  Sell directly to neighborhood customers or list across the open national e-commerce network.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Option A: ONDC */}
                <div className="bg-white border border-[#79563F]/20 rounded-2xl p-5 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-[#1C1917] font-['Outfit']">ONDC Network Listing</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30">
                        Ready for integration
                      </span>
                    </div>
                    <p className="text-xs text-[#79563F] leading-relaxed">
                      List your products on ONDC to reach buyers across buyer apps like Paytm, Magicpin, and pincode-level aggregators with zero platform commissions.
                    </p>
                  </div>

                  <div className="pt-3 border-t border-[#79563F]/15 flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-[#79563F]">Zero commission catalog</span>
                    <button
                      type="button"
                      onClick={() => alert('ONDC Integration onboarding is queued for activation. Catalog mapping prepared.')}
                      className="saffron-gradient-btn px-4 py-2 rounded-xl text-xs font-bold cursor-pointer"
                    >
                      Connect to ONDC
                    </button>
                  </div>
                </div>

                {/* Option B: KALPA Storefront */}
                <div className="bg-white border border-[#79563F]/20 rounded-2xl p-5 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-[#1C1917] font-['Outfit']">KALPA Direct Storefront</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/30">
                        Active Workspace
                      </span>
                    </div>
                    <p className="text-xs text-[#79563F] leading-relaxed">
                      Your complete direct-to-consumer online store with instant WhatsApp order routing, product catalog, customer management, and UPI QR checkout.
                    </p>
                  </div>

                  <div className="pt-3 border-t border-[#79563F]/15 flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-[#79563F]">Complete management suite</span>
                    <button
                      type="button"
                      onClick={() => setActiveView('storefront')}
                      className="px-4 py-2 rounded-xl bg-[#1B4D3E] text-white text-xs font-bold transition cursor-pointer shadow-xs"
                    >
                      Open Storefront Workspace →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 9: ORDERS
              ========================================================== */}
          {activeView === 'orders' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="pb-3 border-b border-[#79563F]/15 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                    <ShoppingCart className="w-4 h-4 text-[#79563F]" />
                    <span>Customer Orders &amp; Fulfillment</span>
                  </h3>
                  <p className="text-xs text-[#79563F] mt-0.5">
                    Incoming doorstep orders and status progression.
                  </p>
                </div>
                <span className="text-xs font-bold text-[#79563F]">{pendingOrdersCount} Active</span>
              </div>

              <div className="space-y-2.5">
                {storeOrders.map((ord) => (
                  <div
                    key={ord.id}
                    className="p-4 rounded-2xl bg-white border border-[#79563F]/15 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[#1C1917]">{ord.id}</span>
                        <span className="text-[10px] text-[#79563F]">({ord.time})</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                          ord.status === 'New'
                            ? 'bg-amber-50 border-amber-300 text-amber-900'
                            : ord.status === 'Accepted'
                            ? 'bg-[#EAF5EE] border-[#1B4D3E]/30 text-[#1B4D3E]'
                            : 'bg-[#FAF7F2] border-[#79563F]/20 text-[#79563F]'
                        }`}>
                          {ord.status}
                        </span>
                      </div>
                      <p className="font-semibold text-xs text-[#1C1917]">{ord.customer} · {ord.locality}</p>
                      <p className="text-[11px] text-[#79563F]">{ord.items}</p>
                      <p className="text-[10px] text-[#79563F]">Delivery Slot: {ord.deliverySlot}</p>
                    </div>

                    <div className="flex items-center gap-3 self-end sm:self-center shrink-0">
                      <span className="font-bold font-['Outfit'] text-base text-[#1B4D3E]">₹{ord.amount}</span>
                      {ord.status === 'New' && (
                        <button
                          type="button"
                          onClick={() => handleUpdateOrderStatus(ord.id, 'Accepted')}
                          className="saffron-gradient-btn px-3.5 py-1.5 rounded-xl text-xs font-bold cursor-pointer"
                        >
                          Accept Order
                        </button>
                      )}
                      {ord.status === 'Accepted' && (
                        <button
                          type="button"
                          onClick={() => handleUpdateOrderStatus(ord.id, 'Dispatched')}
                          className="px-3.5 py-1.5 rounded-xl bg-[#1B4D3E] text-white text-xs font-bold cursor-pointer"
                        >
                          Mark Dispatched
                        </button>
                      )}
                      {ord.status === 'Dispatched' && (
                        <button
                          type="button"
                          onClick={() => handleUpdateOrderStatus(ord.id, 'Delivered')}
                          className="px-3.5 py-1.5 rounded-xl bg-[#FAF7F2] text-[#1B4D3E] border border-[#1B4D3E]/30 text-xs font-bold cursor-pointer"
                        >
                          Mark Delivered
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 10: GROWTH ADVISOR
              ========================================================== */}
          {activeView === 'growth' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="pb-3 border-b border-[#79563F]/15">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#1B4D3E]" />
                  <span>KALPA Growth Advisor</span>
                </h3>
                <p className="text-xs text-[#79563F] mt-0.5">
                  Strategic business development opportunities derived from validated financial models.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 text-xs">
                <div className="bg-white p-4 rounded-2xl border border-[#79563F]/15 space-y-2">
                  <span className="text-[11px] font-bold text-[#1B4D3E] uppercase tracking-wider">1. Route Density Expansion</span>
                  <p className="font-semibold text-sm text-[#1C1917]">+₹16,200/mo Revenue</p>
                  <p className="text-[11px] text-[#79563F] leading-relaxed">
                    Expanding morning delivery by 12 household points in Sector 4 maximizes delivery route vehicle utilization.
                  </p>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-[#79563F]/15 space-y-2">
                  <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">2. Value-Added Dairy Conversion</span>
                  <p className="font-semibold text-sm text-[#1C1917]">48% Gross Margin on Ghee</p>
                  <p className="text-[11px] text-[#79563F] leading-relaxed">
                    Converting 20% surplus milk to A2 Ghee yields higher profit margins than bulk raw milk liquidation.
                  </p>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-[#79563F]/15 space-y-2">
                  <span className="text-[11px] font-bold text-[#C86D3B] uppercase tracking-wider">3. Institutional Term Lock</span>
                  <p className="font-semibold text-sm text-[#1C1917]">Assured Cash Flow</p>
                  <p className="text-[11px] text-[#79563F] leading-relaxed">
                    Renewing 6-month contract with Hotel Shanti Sagar covers 100% of the monthly term loan EMI obligation.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ==========================================================
              VIEW 11: ASK KALPA (OPERATING ASSISTANT EMBEDDED)
              ========================================================== */}
          {activeView === 'assistant' && (
            <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
              <div className="pb-3 border-b border-[#79563F]/15">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
                  <MessageCircle className="w-4 h-4 text-[#1B4D3E]" />
                  <span>Ask KALPA · Business Operating Assistant</span>
                </h3>
                <p className="text-xs text-[#79563F] mt-0.5">
                  Get factual guidance on cash runway, supplier terms, inventory thresholds, and pricing.
                </p>
              </div>

              {/* Chat View */}
              <div className="bg-white border border-[#79563F]/15 rounded-2xl p-4 h-96 overflow-y-auto space-y-3 text-xs">
                {assistantMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl p-3 leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-[#1B4D3E] text-white'
                          : 'bg-[#FAF7F2] border border-[#79563F]/20 text-[#1C1917]'
                      }`}
                    >
                      <p className="whitespace-pre-line">{msg.text}</p>
                    </div>
                  </div>
                ))}
                {assistantLoading && (
                  <div className="flex justify-start">
                    <div className="bg-[#FAF7F2] border border-[#79563F]/20 rounded-2xl p-3 text-xs text-[#79563F] flex items-center gap-2">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#79563F]" />
                      <span>Reviewing operating records...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleAssistantSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={assistantInput}
                  onChange={(e) => setAssistantInput(e.target.value)}
                  placeholder="Ask a business decision question..."
                  className="flex-1 px-4 py-2.5 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                />
                <button
                  type="submit"
                  disabled={!assistantInput.trim() || assistantLoading}
                  className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-2xs cursor-pointer disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send</span>
                </button>
              </form>
            </div>
          )}

          {/* ==========================================================
              VIEW 12: COMPLETE KALPA STOREFRONT MANAGEMENT WORKSPACE
              ========================================================== */}
          {activeView === 'storefront' && (
            <div className="space-y-4 animate-fadeIn">
              {/* Storefront Workspace Header */}
              <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-4 sm:p-5 shadow-2xs space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setActiveView('health')}
                        className="text-xs text-[#79563F] hover:text-[#1C1917] hover:underline flex items-center gap-1 font-semibold cursor-pointer"
                      >
                        <ArrowLeft className="w-3.5 h-3.5" />
                        <span>Growth Manager</span>
                      </button>
                      <span className="text-[#79563F]/60">/</span>
                      <span className="text-xs font-bold text-[#1B4D3E] uppercase tracking-wider">
                        KALPA STOREFRONT
                      </span>
                    </div>
                    <h2 className="text-xl sm:text-2xl font-bold text-[#1C1917] font-['Outfit'] mt-0.5">
                      {businessName} Storefront
                    </h2>
                    <p className="text-xs text-[#79563F]">
                      Online Store Status: <span className="text-[#1B4D3E] font-bold">● Active / Ready</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => alert(`Storefront live link: https://kalpa.market/${businessName.toLowerCase().replace(/[^a-z0-9]/g, '-')}`)}
                      className="px-3.5 py-1.5 rounded-xl bg-white hover:bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/30 text-xs font-bold cursor-pointer flex items-center gap-1.5"
                    >
                      <Globe className="w-3.5 h-3.5" />
                      <span>View Storefront</span>
                    </button>
                  </div>
                </div>

                {/* Storefront Internal Navigation Bar */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar border-t border-[#79563F]/15 pt-3">
                  {[
                    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
                    { id: 'products', label: 'Products', icon: Package },
                    { id: 'inventory', label: 'Inventory', icon: Layers },
                    { id: 'orders', label: 'Orders', icon: ShoppingCart },
                    { id: 'customers', label: 'Customers', icon: Users },
                    { id: 'reviews', label: 'Reviews', icon: Star },
                    { id: 'offers', label: 'Offers', icon: Tag },
                    { id: 'settings', label: 'Store Settings', icon: Settings },
                    { id: 'advisor', label: 'Storefront Advisor', icon: Lightbulb },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    const isActive = storefrontTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        type="button"
                        onClick={() => setStorefrontTab(tab.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                          isActive
                            ? 'bg-[#79563F] text-white shadow-2xs'
                            : 'bg-white/80 text-[#79563F] hover:bg-white border border-[#79563F]/15'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span>{tab.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* STOREFRONT TAB: OVERVIEW */}
              {storefrontTab === 'overview' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
                    <div className="bg-[#FAF2E3] p-3 rounded-2xl border border-[#79563F]/20 text-xs">
                      <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Today's Orders</span>
                      <span className="text-lg font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">3</span>
                      <span className="text-[10px] text-[#1B4D3E]">All assigned</span>
                    </div>

                    <div className="bg-[#FAF2E3] p-3 rounded-2xl border border-[#79563F]/20 text-xs">
                      <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Store Revenue</span>
                      <span className="text-lg font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">₹2,482</span>
                      <span className="text-[10px] text-[#79563F]">Today</span>
                    </div>

                    <div className="bg-[#FAF2E3] p-3 rounded-2xl border border-[#79563F]/20 text-xs">
                      <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Products Listed</span>
                      <span className="text-lg font-bold text-[#1C1917] font-['Outfit'] block mt-0.5">{inventory.length}</span>
                      <span className="text-[10px] text-[#1B4D3E]">Live in catalog</span>
                    </div>

                    <div className="bg-[#FAF2E3] p-3 rounded-2xl border border-[#79563F]/20 text-xs">
                      <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Pending Orders</span>
                      <span className="text-lg font-bold text-[#C86D3B] font-['Outfit'] block mt-0.5">{pendingOrdersCount}</span>
                      <span className="text-[10px] text-[#C86D3B]">Require action</span>
                    </div>

                    <div className="bg-[#FAF2E3] p-3 rounded-2xl border border-[#79563F]/20 text-xs">
                      <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Low Stock</span>
                      <span className="text-lg font-bold text-amber-700 font-['Outfit'] block mt-0.5">1</span>
                      <span className="text-[10px] text-amber-700">Artisanal Paneer</span>
                    </div>

                    <div className="bg-[#FAF2E3] p-3 rounded-2xl border border-[#79563F]/20 text-xs">
                      <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">Rating</span>
                      <span className="text-lg font-bold text-[#1B4D3E] font-['Outfit'] block mt-0.5">4.8 ★</span>
                      <span className="text-[10px] text-[#79563F]">3 Verified Reviews</span>
                    </div>
                  </div>

                  {/* Store Activity + AI Recommendations */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 space-y-2.5 text-xs">
                      <span className="font-bold text-[#1C1917] block uppercase tracking-wider text-[11px]">Recent Store Activity</span>
                      <div className="space-y-2">
                        <div className="p-2.5 rounded-xl bg-white border border-[#79563F]/15">
                          <span className="font-semibold text-[#1C1917] block">Order #ORD-901 Received</span>
                          <span className="text-[11px] text-[#79563F]">Priya Sharma ordered 2L Fresh Milk + Curd (₹162)</span>
                        </div>
                        <div className="p-2.5 rounded-xl bg-white border border-[#79563F]/15">
                          <span className="font-semibold text-[#1C1917] block">Review Received</span>
                          <span className="text-[11px] text-[#79563F]">5★ rating from Rajesh Patil for Traditional Ghee</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 space-y-2.5 text-xs">
                      <span className="font-bold text-[#1C1917] block uppercase tracking-wider text-[11px]">Storefront Operating Insights</span>
                      <div className="space-y-2 text-[11px] text-[#79563F]">
                        <div className="p-2.5 rounded-xl bg-white border border-[#79563F]/15">
                          <span className="font-bold text-[#1B4D3E] block">Demand Surge on Fresh Cow Milk</span>
                          <span>Fresh Cow Milk received +25% more inquiries this week. Consider preparing extra 20L for morning slots.</span>
                        </div>
                        <div className="p-2.5 rounded-xl bg-white border border-[#79563F]/15">
                          <span className="font-bold text-[#C86D3B] block">Delivery Timing Feedback</span>
                          <span>Customer Sunita Joshi noted delivery timing preferences before 6:30 AM for morning routes.</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* STOREFRONT TAB: PRODUCTS */}
              {storefrontTab === 'products' && (
                <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 shadow-2xs space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-[#79563F]/15">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917]">
                      Storefront Product Catalog
                    </h3>
                    <button
                      type="button"
                      onClick={() => setAddProductModalOpen(true)}
                      className="saffron-gradient-btn px-3.5 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Product</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {inventory.map((prod) => (
                      <div key={prod.id} className="bg-white p-4 rounded-2xl border border-[#79563F]/15 space-y-2 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] font-bold text-[#79563F]">{prod.category}</span>
                          <span className="text-[10px] font-bold text-[#1B4D3E] bg-[#EAF5EE] px-2 py-0.5 rounded-md">Live</span>
                        </div>
                        <h4 className="font-bold text-sm text-[#1C1917]">{prod.name}</h4>
                        <div className="flex justify-between text-[#79563F] pt-1">
                          <span>Price: <strong className="text-[#1C1917]">₹{prod.sellingPrice}/{prod.unit}</strong></span>
                          <span>Stock: <strong className="text-[#1C1917]">{prod.quantity}</strong></span>
                        </div>
                        <div className="text-[10px] text-[#79563F]">Total store orders: {prod.ordersCount}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STOREFRONT TAB: INVENTORY */}
              {storefrontTab === 'inventory' && (
                <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 shadow-2xs space-y-3 text-xs">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917] pb-2 border-b border-[#79563F]/15">
                    Store Inventory Levels
                  </h3>
                  <div className="space-y-2">
                    {inventory.map((item) => (
                      <div key={item.id} className="p-3 bg-white rounded-xl border border-[#79563F]/15 flex items-center justify-between">
                        <div>
                          <span className="font-bold text-[#1C1917] block">{item.name}</span>
                          <span className="text-[10px] text-[#79563F]">SKU: {item.sku}</span>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-sm text-[#1C1917] block">{item.quantity} {item.unit}</span>
                          <span className={`text-[10px] font-semibold ${item.status === 'In Stock' ? 'text-[#1B4D3E]' : 'text-amber-700'}`}>
                            {item.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STOREFRONT TAB: ORDERS */}
              {storefrontTab === 'orders' && (
                <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 shadow-2xs space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917] pb-2 border-b border-[#79563F]/15">
                    Active Store Orders
                  </h3>
                  <div className="space-y-2">
                    {storeOrders.map((ord) => (
                      <div key={ord.id} className="p-3.5 bg-white rounded-xl border border-[#79563F]/15 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[#1C1917]">{ord.id}</span>
                            <span className="text-[10px] text-[#79563F]">{ord.customer} ({ord.locality})</span>
                          </div>
                          <p className="text-[11px] text-[#79563F] mt-0.5">{ord.items}</p>
                        </div>
                        <div className="flex items-center gap-3 self-end sm:self-center">
                          <span className="font-bold text-sm text-[#1B4D3E] font-['Outfit']">₹{ord.amount}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-[#FAF7F2] border border-[#79563F]/20 text-[#79563F]">{ord.status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STOREFRONT TAB: CUSTOMERS */}
              {storefrontTab === 'customers' && (
                <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 shadow-2xs space-y-3 text-xs">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917] pb-2 border-b border-[#79563F]/15">
                    Registered Customers &amp; Subscribers
                  </h3>
                  <div className="space-y-2">
                    {storeCustomers.map((c) => (
                      <div key={c.id} className="p-3 bg-white rounded-xl border border-[#79563F]/15 flex items-center justify-between">
                        <div>
                          <span className="font-bold text-[#1C1917] block">{c.name}</span>
                          <span className="text-[10px] text-[#79563F]">{c.locality} · {c.phone}</span>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-[#1B4D3E] block">₹{c.totalSpent.toLocaleString('en-IN')}</span>
                          <span className="text-[10px] text-[#79563F]">{c.ordersCount} orders</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STOREFRONT TAB: REVIEWS */}
              {storefrontTab === 'reviews' && (
                <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 shadow-2xs space-y-3 text-xs">
                  <div className="pb-2 border-b border-[#79563F]/15">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917]">
                      Customer Reviews &amp; Feedback Summary
                    </h3>
                  </div>

                  {/* AI Feedback Summary */}
                  <div className="p-3.5 rounded-xl bg-[#EAF5EE] border border-[#1B4D3E]/30 text-[#1B4D3E] space-y-1">
                    <span className="font-bold uppercase tracking-wider text-[10px] block">Customer Feedback Summary</span>
                    <p className="text-xs leading-relaxed">
                      "Customers consistently rate milk and ghee quality as 5/5 stars for purity. Operational recommendation: standardise early morning route to guarantee arrivals before 6:30 AM."
                    </p>
                  </div>

                  <div className="space-y-2 pt-1">
                    {storeReviews.map((r) => (
                      <div key={r.id} className="p-3 bg-white rounded-xl border border-[#79563F]/15 space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-[#1C1917]">{r.customer}</span>
                          <span className="text-[#C86D3B] font-bold">{'★'.repeat(r.rating)}</span>
                        </div>
                        <p className="text-[11px] text-[#79563F]">{r.comment}</p>
                        <span className="text-[10px] text-[#79563F]/70 block">{r.date}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STOREFRONT TAB: OFFERS */}
              {storefrontTab === 'offers' && (
                <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 shadow-2xs space-y-4 text-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-[#79563F]/15">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917]">
                      Active Promotions &amp; Discounts
                    </h3>
                    <button
                      type="button"
                      onClick={() => setCreateOfferModalOpen(true)}
                      className="saffron-gradient-btn px-3 py-1.5 rounded-xl text-xs font-bold cursor-pointer"
                    >
                      + Create Offer
                    </button>
                  </div>

                  <div className="space-y-2">
                    {storeOffers.map((off) => (
                      <div key={off.id} className="p-3.5 bg-white rounded-xl border border-[#79563F]/15 flex items-center justify-between">
                        <div>
                          <span className="font-bold text-[#1C1917] block">{off.name}</span>
                          <span className="text-[11px] text-[#79563F]">{off.discount} (Code: <strong>{off.code}</strong>)</span>
                        </div>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30">
                          Active
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STOREFRONT TAB: SETTINGS */}
              {storefrontTab === 'settings' && (
                <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 shadow-2xs space-y-3 text-xs">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917] pb-2 border-b border-[#79563F]/15">
                    Storefront Operational Settings
                  </h3>

                  <div className="space-y-2 text-[#79563F]">
                    <div className="p-3 bg-white rounded-xl border border-[#79563F]/15">
                      <span className="font-bold text-[#1C1917] block">Delivery Coverage Radius</span>
                      <span>5.0 km from processing farm</span>
                    </div>

                    <div className="p-3 bg-white rounded-xl border border-[#79563F]/15">
                      <span className="font-bold text-[#1C1917] block">Accepted Payment Methods</span>
                      <span>UPI QR (Instant Bank Settlement), Cash on Delivery (COD)</span>
                    </div>

                    <div className="p-3 bg-white rounded-xl border border-[#79563F]/15">
                      <span className="font-bold text-[#1C1917] block">Store Operational Hours</span>
                      <span>Morning: 5:30 AM – 9:00 AM | Evening: 4:30 PM – 7:30 PM</span>
                    </div>
                  </div>
                </div>
              )}

              {/* STOREFRONT TAB: ADVISOR */}
              {storefrontTab === 'advisor' && (
                <div className="bg-[#FAF2E3] border border-[#79563F]/25 rounded-3xl p-5 shadow-2xs space-y-3 text-xs">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917] pb-2 border-b border-[#79563F]/15">
                    Storefront Operating Advisor
                  </h3>

                  <div className="space-y-2">
                    <div className="p-3.5 bg-white rounded-xl border border-[#79563F]/15 space-y-1">
                      <span className="font-bold text-[#1B4D3E] block">Which product should I promote?</span>
                      <p className="text-[#79563F] leading-relaxed">
                        Traditional Cultured Ghee (A2) yields a 48% gross margin. Promoting 1kg packs ahead of weekend festivities will maximize net earnings per litre of processed milk.
                      </p>
                    </div>

                    <div className="p-3.5 bg-white rounded-xl border border-[#79563F]/15 space-y-1">
                      <span className="font-bold text-[#1B4D3E] block">How to improve morning delivery satisfaction?</span>
                      <p className="text-[#79563F] leading-relaxed">
                        Setting departure time to 5:45 AM rather than 6:15 AM ensures all 145 household doorstep deliveries complete before 7:00 AM, resolving customer timing remarks.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* ============================================================
          3. "ASK KALPA" BUSINESS ASSISTANT SLIDE-OVER DRAWER
          ============================================================ */}
      {assistantDrawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-lg bg-[#FAF7F2] border-l border-[#79563F]/30 h-full flex flex-col shadow-2xl">
            <div className="p-5 bg-[#FAF2E3] border-b border-[#79563F]/20 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base text-[#1C1917] font-['Outfit']">
                  KALPA Business Operating Assistant
                </h3>
                <p className="text-xs text-[#79563F] mt-0.5">
                  Advisory on cash flow, inventory, demand &amp; supplier decisions
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAssistantDrawerOpen(false)}
                className="p-1.5 rounded-lg hover:bg-white/60 text-[#79563F] hover:text-[#1C1917] font-bold text-base cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div ref={assistantScrollRef} className="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs">
              {assistantMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-3.5 leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-[#1B4D3E] text-white shadow-2xs'
                        : 'bg-white border border-[#79563F]/20 text-[#1C1917] shadow-2xs'
                    }`}
                  >
                    <p className="whitespace-pre-line">{msg.text}</p>
                  </div>
                </div>
              ))}
              {assistantLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-[#79563F]/20 rounded-2xl p-3 text-xs text-[#79563F] flex items-center gap-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#79563F]" />
                    <span>Reviewing business profile &amp; cash models...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Prompts */}
            <div className="p-3 bg-[#FAF2E3]/70 border-t border-[#79563F]/15 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
              {[
                'How is my cash buffer for next week?',
                'Should I approve the feed supplier order?',
                'How to increase morning retail margins?',
              ].map((prompt, pIdx) => (
                <button
                  key={pIdx}
                  type="button"
                  onClick={() => handleAssistantSend(prompt)}
                  className="px-2.5 py-1 rounded-lg bg-white border border-[#79563F]/20 text-[11px] text-[#79563F] hover:bg-[#FAF7F2] font-semibold shrink-0 cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="p-4 bg-white border-t border-[#79563F]/20">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleAssistantSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={assistantInput}
                  onChange={(e) => setAssistantInput(e.target.value)}
                  placeholder="Ask a business decision question..."
                  className="flex-1 px-4 py-2.5 rounded-xl bg-[#FAF7F2] border border-[#79563F]/30 text-xs text-[#1C1917] focus:outline-none focus:ring-2 focus:ring-[#79563F]/25"
                />
                <button
                  type="submit"
                  disabled={!assistantInput.trim() || assistantLoading}
                  className="saffron-gradient-btn px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-2xs cursor-pointer disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================
          4. ADD PRODUCT MODAL
          ============================================================ */}
      {addProductModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/40 backdrop-blur-xs animate-fadeIn">
          <div className="bg-[#FAF7F2] border border-[#79563F]/30 rounded-3xl w-full max-w-md p-5 sm:p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-[#79563F]/15">
              <h4 className="font-bold text-base text-[#1C1917] font-['Outfit']">
                Add Product to Inventory
              </h4>
              <button
                type="button"
                onClick={() => setAddProductModalOpen(false)}
                className="text-[#79563F] hover:text-[#1C1917] font-bold text-base cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Photo / Voice Smart Capture */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <label className="p-3 rounded-xl bg-[#FAF2E3] border border-[#79563F]/25 flex items-center justify-center gap-2 cursor-pointer hover:bg-white transition">
                <Camera className="w-4 h-4 text-[#79563F]" />
                <span className="font-semibold text-[#79563F]">
                  {photoUploading ? 'Analyzing...' : 'Photo Input'}
                </span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoAdd}
                  className="hidden"
                />
              </label>

              <button
                type="button"
                onClick={handleVoiceAddToggle}
                className={`p-3 rounded-xl border flex items-center justify-center gap-2 cursor-pointer transition ${
                  voiceRecording
                    ? 'bg-red-50 border-red-300 text-red-700 animate-pulse'
                    : 'bg-[#FAF2E3] border-[#79563F]/25 text-[#79563F] hover:bg-white'
                }`}
              >
                {voiceRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                <span className="font-semibold text-xs">
                  {voiceRecording ? 'Listening...' : 'Voice Input'}
                </span>
              </button>
            </div>

            {/* Inputs */}
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                  Product Name
                </label>
                <input
                  type="text"
                  value={draftProduct.name}
                  onChange={(e) => setDraftProduct({ ...draftProduct, name: e.target.value })}
                  placeholder="e.g. Organic Buffalo Curd"
                  className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                />
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                    Category
                  </label>
                  <select
                    value={draftProduct.category}
                    onChange={(e) => setDraftProduct({ ...draftProduct, category: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                  >
                    <option value="Dairy Products">Dairy Products</option>
                    <option value="Processed Dairy">Processed Dairy</option>
                    <option value="Fresh Cheese">Fresh Cheese</option>
                    <option value="Raw Materials">Raw Materials</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                    Initial Stock
                  </label>
                  <input
                    type="number"
                    value={draftProduct.quantity}
                    onChange={(e) => setDraftProduct({ ...draftProduct, quantity: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                    Purchase Cost (₹)
                  </label>
                  <input
                    type="number"
                    value={draftProduct.purchaseCost}
                    onChange={(e) => setDraftProduct({ ...draftProduct, purchaseCost: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                    Selling Price (₹)
                  </label>
                  <input
                    type="number"
                    value={draftProduct.sellingPrice}
                    onChange={(e) => setDraftProduct({ ...draftProduct, sellingPrice: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#79563F]/15">
              <button
                type="button"
                onClick={() => setAddProductModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-white text-[#79563F] border border-[#79563F]/30 text-xs font-bold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!draftProduct.name.trim()}
                onClick={handleConfirmAddProduct}
                className="saffron-gradient-btn px-5 py-2 rounded-xl text-xs font-bold cursor-pointer disabled:opacity-50"
              >
                Add Product
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================
          5. RECORD TRANSACTION MODAL
          ============================================================ */}
      {transactionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/40 backdrop-blur-xs animate-fadeIn">
          <div className="bg-[#FAF7F2] border border-[#79563F]/30 rounded-3xl w-full max-w-md p-5 sm:p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-[#79563F]/15">
              <h4 className="font-bold text-base text-[#1C1917] font-['Outfit']">
                Record Operating Cash Entry
              </h4>
              <button
                type="button"
                onClick={() => setTransactionModalOpen(false)}
                className="text-[#79563F] hover:text-[#1C1917] font-bold text-base cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                    Entry Type
                  </label>
                  <select
                    value={draftTransaction.type}
                    onChange={(e) => setDraftTransaction({ ...draftTransaction, type: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                  >
                    <option value="Inflow">Cash Inflow (+)</option>
                    <option value="Outflow">Cash Outflow (-)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                    Category
                  </label>
                  <select
                    value={draftTransaction.category}
                    onChange={(e) => setDraftTransaction({ ...draftTransaction, category: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                  >
                    <option value="Retail Sales">Retail Sales</option>
                    <option value="B2B Wholesale">B2B Wholesale</option>
                    <option value="Raw Materials">Raw Materials / Feed</option>
                    <option value="Utilities">Utilities &amp; Power</option>
                    <option value="Transport">Transport &amp; Fuel</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={draftTransaction.description}
                  onChange={(e) => setDraftTransaction({ ...draftTransaction, description: e.target.value })}
                  placeholder="e.g. Counter sales / Feed delivery fuel"
                  className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                  Amount (₹)
                </label>
                <input
                  type="number"
                  value={draftTransaction.amount}
                  onChange={(e) => setDraftTransaction({ ...draftTransaction, amount: e.target.value })}
                  placeholder="e.g. 4500"
                  className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#79563F]/15">
              <button
                type="button"
                onClick={() => setTransactionModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-white text-[#79563F] border border-[#79563F]/30 text-xs font-bold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!draftTransaction.description.trim() || !draftTransaction.amount}
                onClick={handleAddTransaction}
                className="saffron-gradient-btn px-5 py-2 rounded-xl text-xs font-bold cursor-pointer disabled:opacity-50"
              >
                Save Entry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================
          6. CREATE OFFER MODAL
          ============================================================ */}
      {createOfferModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/40 backdrop-blur-xs animate-fadeIn">
          <div className="bg-[#FAF7F2] border border-[#79563F]/30 rounded-3xl w-full max-w-md p-5 sm:p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-[#79563F]/15">
              <h4 className="font-bold text-base text-[#1C1917] font-['Outfit']">
                Create Store Promotion / Offer
              </h4>
              <button
                type="button"
                onClick={() => setCreateOfferModalOpen(false)}
                className="text-[#79563F] hover:text-[#1C1917] font-bold text-base cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                  Offer Name
                </label>
                <input
                  type="text"
                  value={draftOffer.name}
                  onChange={(e) => setDraftOffer({ ...draftOffer, name: e.target.value })}
                  placeholder="e.g. Weekend Ghee Special"
                  className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                  Discount Details
                </label>
                <input
                  type="text"
                  value={draftOffer.discount}
                  onChange={(e) => setDraftOffer({ ...draftOffer, discount: e.target.value })}
                  placeholder="e.g. 5% off on 1kg pack"
                  className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                  Promo Code
                </label>
                <input
                  type="text"
                  value={draftOffer.code}
                  onChange={(e) => setDraftOffer({ ...draftOffer, code: e.target.value })}
                  placeholder="e.g. GHEE5"
                  className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#79563F]/30 text-xs text-[#1C1917]"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#79563F]/15">
              <button
                type="button"
                onClick={() => setCreateOfferModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-white text-[#79563F] border border-[#79563F]/30 text-xs font-bold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!draftOffer.name || !draftOffer.discount}
                onClick={handleAddOffer}
                className="saffron-gradient-btn px-5 py-2 rounded-xl text-xs font-bold cursor-pointer disabled:opacity-50"
              >
                Publish Offer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================
          7. BUSINESS SETTINGS MODAL
          ============================================================ */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/40 backdrop-blur-xs animate-fadeIn">
          <div className="bg-[#FAF7F2] border border-[#79563F]/30 rounded-3xl w-full max-w-lg p-5 sm:p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-[#79563F]/15">
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-[#79563F]" />
                <h4 className="font-bold text-base text-[#1C1917] font-['Outfit']">
                  Business Settings &amp; Bank Link
                </h4>
              </div>
              <button
                type="button"
                onClick={() => setShowSettingsModal(false)}
                className="text-[#79563F] hover:text-[#1C1917] font-bold text-base cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-[#79563F]">
              <div className="bg-white p-3.5 rounded-xl border border-[#79563F]/15 space-y-1">
                <span className="font-bold text-[#1C1917] block">Enterprise Name</span>
                <p className="text-xs">{businessName}</p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-[#79563F]/15 space-y-1">
                <span className="font-bold text-[#1C1917] block">Bank Term Loan Linked</span>
                <p className="text-xs">
                  Sanctioned Amount: ₹{financialMetrics.termLoan.toLocaleString('en-IN')} · Monthly EMI: ₹{financialMetrics.emi.toLocaleString('en-IN')}
                </p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-[#79563F]/15 space-y-1">
                <span className="font-bold text-[#1C1917] block">Operating Security &amp; Isolation</span>
                <p className="text-xs leading-relaxed">
                  Canonical business scenario `{scenarioId}`. All actions require explicit promoter authorization.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end pt-2 border-t border-[#79563F]/15">
              <button
                type="button"
                onClick={() => setShowSettingsModal(false)}
                className="saffron-gradient-btn px-5 py-2 rounded-xl text-xs font-bold cursor-pointer"
              >
                Close Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GrowthManagerPage;
