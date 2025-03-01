import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { setCurrentView, setSelectedCompany } from '../store/simulationSlice';
import { companies } from '../store/knowledgeBaseData';
import { Company, CompanyNews, CompanyDocument } from '../models/types';

const KnowledgeBase: React.FC = () => {
  const dispatch = useDispatch();
  const selectedCompanyId = useSelector((state: RootState) => state.simulation.selectedCompany);
  
  // Find the selected company data
  const selectedCompany = companies.find(company => company.id === selectedCompanyId) || companies[0];
  
  // Handle company selection
  const handleSelectCompany = (companyId: string) => {
    dispatch(setSelectedCompany(companyId));
  };
  
  // Return to office view
  const handleReturnToOffice = () => {
    dispatch(setCurrentView('office'));
  };
  
  // Render a news item
  const renderNewsItem = (news: CompanyNews) => {
    const impactColor = news.impact === 'positive' 
      ? '#4caf50' 
      : news.impact === 'negative' 
        ? '#f44336' 
        : '#2196f3';
    
    return (
      <div 
        key={news.id} 
        style={{
          padding: '10px',
          marginBottom: '10px',
          background: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '5px',
          borderLeft: `5px solid ${impactColor}`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <span style={{ fontWeight: 'bold' }}>{news.headline}</span>
          <span style={{ fontSize: '0.8em', color: '#666' }}>{news.date}</span>
        </div>
        <p style={{ margin: '5px 0', fontSize: '0.9em' }}>{news.summary}</p>
      </div>
    );
  };
  
  // Render a document item
  const renderDocumentItem = (doc: CompanyDocument) => {
    const iconMap = {
      pdf: '📄',
      spreadsheet: '📊',
      presentation: '📝',
    };
    
    return (
      <div 
        key={doc.id} 
        style={{
          padding: '10px',
          marginBottom: '10px',
          background: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '5px',
          display: 'flex',
          alignItems: 'center',
          cursor: 'pointer',
        }}
        onClick={() => console.log(`Document clicked: ${doc.id}`)}
      >
        <div style={{ fontSize: '24px', marginRight: '10px' }}>{iconMap[doc.type]}</div>
        <div>
          <div style={{ fontWeight: 'bold' }}>{doc.title}</div>
          <div style={{ fontSize: '0.8em', color: '#666' }}>{doc.description}</div>
        </div>
      </div>
    );
  };
  
  // Render financials table
  const renderFinancials = (financials: Company['financials']) => {
    const items = [
      { label: 'Revenue', value: financials.revenue },
      { label: 'Profit', value: financials.profit },
      { label: 'Growth Rate', value: financials.growthRate },
      { label: 'P/E Ratio', value: financials.peRatio },
      { label: 'Market Cap', value: financials.marketCap },
      { label: 'Dividend Yield', value: financials.dividendYield },
    ];
    
    return (
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(3, 1fr)', 
        gap: '10px',
        marginBottom: '20px',
      }}>
        {items.map((item, index) => (
          <div 
            key={index} 
            style={{ 
              background: 'rgba(255, 255, 255, 0.8)', 
              padding: '10px', 
              borderRadius: '5px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontWeight: 'bold', fontSize: '0.8em', color: '#666' }}>{item.label}</div>
            <div style={{ fontWeight: 'bold', fontSize: '1.2em' }}>{item.value}</div>
          </div>
        ))}
      </div>
    );
  };
  
  return (
    <div 
      style={{
        width: '100%',
        height: '100vh',
        display: 'flex',
        background: '#f0f0f0',
        fontFamily: 'Arial, sans-serif',
      }}
    >
      {/* Sidebar */}
      <div 
        style={{
          width: '20%',
          height: '100%',
          background: '#263238',
          padding: '20px 10px',
          overflowY: 'auto',
          boxShadow: '2px 0 5px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <h2 style={{ color: 'white', margin: '0 0 5px 0' }}>S&P Companies</h2>
          <div style={{ height: '2px', background: '#4caf50', width: '50%', margin: '0 auto' }}></div>
        </div>
        
        {companies.map(company => (
          <div 
            key={company.id}
            style={{
              padding: '15px 10px',
              margin: '5px 0',
              background: selectedCompanyId === company.id ? 'rgba(76, 175, 80, 0.2)' : 'transparent',
              borderRadius: '5px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              color: 'white',
              borderLeft: selectedCompanyId === company.id ? '4px solid #4caf50' : '4px solid transparent',
            }}
            onClick={() => handleSelectCompany(company.id)}
          >
            <div 
              style={{ 
                width: '30px', 
                height: '30px',
                background: '#4caf50',
                borderRadius: '5px',
                marginRight: '10px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                fontWeight: 'bold',
              }}
            >
              {company.ticker.substring(0, 1)}
            </div>
            <div>
              <div style={{ fontWeight: 'bold' }}>{company.name}</div>
              <div style={{ fontSize: '0.8em', opacity: 0.7 }}>{company.ticker}</div>
            </div>
          </div>
        ))}
        
        <div style={{ marginTop: '30px', padding: '10px' }}>
          <button 
            onClick={handleReturnToOffice}
            style={{
              width: '100%',
              padding: '10px',
              background: '#4caf50',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            Return to Office
          </button>
        </div>
      </div>
      
      {/* Main content */}
      <div 
        style={{
          width: '80%',
          height: '100%',
          padding: '20px',
          overflowY: 'auto',
        }}
      >
        {/* Breadcrumbs */}
        <div style={{ marginBottom: '20px' }}>
          <span 
            style={{ cursor: 'pointer', color: '#4caf50' }}
            onClick={handleReturnToOffice}
          >
            Office
          </span>
          <span style={{ margin: '0 5px' }}>/</span>
          <span style={{ fontWeight: 'bold' }}>Knowledge Base</span>
          <span style={{ margin: '0 5px' }}>/</span>
          <span>{selectedCompany.name}</span>
        </div>
        
        {/* Company header */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '20px',
          }}
        >
          <div 
            style={{ 
              width: '80px', 
              height: '80px',
              background: '#4caf50',
              borderRadius: '10px',
              marginRight: '20px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontWeight: 'bold',
              fontSize: '2em',
              color: 'white',
            }}
          >
            {selectedCompany.ticker.substring(0, 1)}
          </div>
          <div>
            <h1 style={{ margin: '0 0 5px 0' }}>{selectedCompany.name} ({selectedCompany.ticker})</h1>
            <div style={{ color: '#666' }}>
              {selectedCompany.sector} | {selectedCompany.industry}
            </div>
            <div style={{ marginTop: '5px' }}>
              <a 
                href={selectedCompany.website} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: '#4caf50', textDecoration: 'none' }}
              >
                {selectedCompany.website}
              </a>
            </div>
          </div>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          {/* Left column */}
          <div>
            <div 
              style={{ 
                background: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: '10px',
                padding: '20px',
                marginBottom: '20px',
              }}
            >
              <h2 style={{ margin: '0 0 15px 0', color: '#4caf50' }}>Company Overview</h2>
              <p style={{ whiteSpace: 'pre-line', margin: 0, lineHeight: '1.5' }}>
                {selectedCompany.description}
              </p>
            </div>
            
            <div 
              style={{ 
                background: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: '10px',
                padding: '20px',
              }}
            >
              <h2 style={{ margin: '0 0 15px 0', color: '#4caf50' }}>Key Financials</h2>
              {renderFinancials(selectedCompany.financials)}
            </div>
          </div>
          
          {/* Right column */}
          <div>
            <div 
              style={{ 
                background: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: '10px',
                padding: '20px',
                marginBottom: '20px',
              }}
            >
              <h2 style={{ margin: '0 0 15px 0', color: '#4caf50' }}>Recent News</h2>
              {selectedCompany.news.map(renderNewsItem)}
            </div>
            
            <div 
              style={{ 
                background: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: '10px',
                padding: '20px',
              }}
            >
              <h2 style={{ margin: '0 0 15px 0', color: '#4caf50' }}>Documents</h2>
              {selectedCompany.documents.map(renderDocumentItem)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBase;