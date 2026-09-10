import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Footer from './Footer';
import ContourBackground from '../ui/ContourBackground';

export const Layout = () => {
  return (
    <div className="flex flex-col min-h-screen relative bg-[#FAF7F2] text-[#1C1917]">
      <ContourBackground />
      <div className="relative z-10 flex flex-col flex-grow">
        <Navbar />
        <main className="flex-grow pt-24 pb-12">
          <Outlet />
        </main>
        <Footer />
      </div>
    </div>
  );
};

export default Layout;
