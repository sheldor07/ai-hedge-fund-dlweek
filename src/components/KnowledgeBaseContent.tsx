import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { setSelectedCompany } from '../store/simulationSlice';
import { companies } from '../store/knowledgeBaseData';
import { Company, CompanyNews, CompanyDocument } from '../models/types';

const KnowledgeBaseContent: React.FC = () => {
  const dispatch = useDispatch();
  const selectedCompanyId = useSelector((state: RootState) => state.simulation.selectedCompany);
  
  // Find the selected company data
  const selectedCompany = companies.find(company => company.id === selectedCompanyId) || companies[0];
  
  // Handle company selection
  const handleSelectCompany = (companyId: string) => {
    dispatch(setSelectedCompany(companyId));
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
          padding: '8px',
          marginBottom: '8px',
          background: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '4px',
          borderLeft: `4px solid ${impactColor}`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ fontWeight: 'bold', fontSize: '13px' }}>{news.headline}</span>
          <span style={{ fontSize: '11px', color: '#666' }}>{news.date}</span>
        </div>
        <p style={{ margin: '3px 0', fontSize: '12px' }}>{news.summary}</p>
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
          padding: '8px',
          marginBottom: '8px',
          background: 'rgba(255, 255, 255, 0.8)',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          cursor: 'pointer',
        }}
        onClick={() => console.log(`Document clicked: ${doc.id}`)}
      >
        <div style={{ fontSize: '18px', marginRight: '8px' }}>{iconMap[doc.type]}</div>
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '13px' }}>{doc.title}</div>
          <div style={{ fontSize: '11px', color: '#666' }}>{doc.description}</div>
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
        gap: '8px',
        marginBottom: '15px',
      }}>
        {items.map((item, index) => (
          <div 
            key={index} 
            style={{ 
              background: 'rgba(255, 255, 255, 0.8)', 
              padding: '8px', 
              borderRadius: '4px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontWeight: 'bold', fontSize: '11px', color: '#666' }}>{item.label}</div>
            <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{item.value}</div>
          </div>
        ))}
      </div>
    );
  };
  
  return (
    <div 
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        background: '#1e1e1e',
        fontFamily: 'Arial, sans-serif',
        color: '#e0e0e0',
      }}
    >
      {/* Sidebar */}
      <div 
        style={{
          width: '20%',
          height: '100%',
          background: '#2a2a2a',
          padding: '15px 10px',
          overflowY: 'auto',
          borderRight: '1px solid #444',
        }}
      >
        <div style={{ marginBottom: '15px' }}>
          <h3 style={{ color: '#4caf50', margin: '0 0 5px 0', fontSize: '16px' }}>S&P Companies</h3>
          <div style={{ height: '2px', background: '#4caf50', width: '50%' }}></div>
        </div>
        
        {companies.map(company => (
          <div 
            key={company.id}
            style={{
              padding: '10px 8px',
              margin: '4px 0',
              background: selectedCompanyId === company.id ? 'rgba(76, 175, 80, 0.2)' : 'transparent',
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              borderLeft: selectedCompanyId === company.id ? '3px solid #4caf50' : '3px solid transparent',
            }}
            onClick={() => handleSelectCompany(company.id)}
          >
            <div 
              style={{ 
                width: '24px', 
                height: '24px',
                background: '#4caf50',
                borderRadius: '4px',
                marginRight: '8px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                fontWeight: 'bold',
                fontSize: '12px',
              }}
            >
              {company.ticker.substring(0, 1)}
            </div>
            <div>
              <div style={{ fontWeight: 'bold', fontSize: '13px' }}>{company.name}</div>
              <div style={{ fontSize: '11px', opacity: 0.7 }}>{company.ticker}</div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Main content */}
      <div 
        style={{
          width: '80%',
          height: '100%',
          padding: '15px',
          overflowY: 'auto',
        }}
      >
        {/* Company header */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '15px',
            padding: '10px',
            background: 'rgba(76, 175, 80, 0.1)',
            borderRadius: '5px',
          }}
        >
          <div 
            style={{ 
              width: '50px', 
              height: '50px',
              background: '#4caf50',
              borderRadius: '6px',
              marginRight: '15px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontWeight: 'bold',
              fontSize: '20px',
            }}
          >
            {selectedCompany.ticker.substring(0, 1)}
          </div>
          <div>
            <h2 style={{ margin: '0 0 3px 0', fontSize: '18px' }}>{selectedCompany.name} ({selectedCompany.ticker})</h2>
            <div style={{ color: '#aaa', fontSize: '13px' }}>
              {selectedCompany.sector} | {selectedCompany.industry}
            </div>
            <div style={{ marginTop: '4px' }}>
              <a 
                href={selectedCompany.website} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: '#4caf50', textDecoration: 'none', fontSize: '12px' }}
              >
                {selectedCompany.website}
              </a>
            </div>
          </div>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          {/* Left column */}
          <div>
            <div 
              style={{ 
                background: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: '5px',
                padding: '15px',
                marginBottom: '15px',
              }}
            >
              <h3 style={{ margin: '0 0 10px 0', color: '#4caf50', fontSize: '16px' }}>Company Overview</h3>
              <p style={{ whiteSpace: 'pre-line', margin: 0, lineHeight: '1.4', fontSize: '13px' }}>
                {selectedCompany.description}
              </p>
            </div>
            
            <div 
              style={{ 
                background: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: '5px',
                padding: '15px',
              }}
            >
              <h3 style={{ margin: '0 0 10px 0', color: '#4caf50', fontSize: '16px' }}>Key Financials</h3>
              {renderFinancials(selectedCompany.financials)}
            </div>
          </div>
          
          {/* Right column */}
          <div>
            <div 
              style={{ 
                background: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: '5px',
                padding: '15px',
                marginBottom: '15px',
              }}
            >
              <h3 style={{ margin: '0 0 10px 0', color: '#4caf50', fontSize: '16px' }}>Recent News</h3>
              {selectedCompany.news.map(renderNewsItem)}
            </div>
            
            <div 
              style={{ 
                background: 'rgba(76, 175, 80, 0.1)', 
                borderRadius: '5px',
                padding: '15px',
              }}
            >
              <h3 style={{ margin: '0 0 10px 0', color: '#4caf50', fontSize: '16px' }}>Documents</h3>
              {selectedCompany.documents.map(renderDocumentItem)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBaseContent;