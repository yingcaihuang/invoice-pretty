import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
        <header className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-2">
            Web Invoice Processor
          </h1>
          <p className="text-base sm:text-lg text-gray-600">
            Process PDF invoices with custom layouts
          </p>
          <p className="text-sm text-red-600 font-bold mt-2">
            Files are temporarily stored for 24 hours and automatically deleted after expiration
          </p>
        </header>
        
        <main>
          {children}
        </main>
        
        <footer className="mt-12 sm:mt-16 text-center text-gray-500 text-sm">
          <p>Web Invoice Processor - Transform your PDF invoices with ease</p>
        </footer>
      </div>
    </div>
  );
};

export default Layout;