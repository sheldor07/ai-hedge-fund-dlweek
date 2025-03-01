```mermaid
graph TB
    %% Main components
    subgraph "Frontend"
        UI["React UI Components"]
        SimEngine["Simulation Engine"]
        TradingSystem["Trading System"]
        CharStore["Character Store"]
        PortStore["Portfolio Store"]
        Events["Event Processor"]
    end
    
    subgraph "Backend Agents"
        CEO["CEO Agent (8010)"]
        Manager["Manager Agent (8000)"]
        Portfolio["Portfolio Manager (8003)"]
        TechAnalysis["Technical Analysis Agent (8002)"]
        FundAnalysis["Fundamental Analysis Agent (8001)"]
    end
    
    subgraph "External Resources"
        MarketData["Market Data APIs"]
        LLM["LLM Services<br>(Claude)"]
        DB["MongoDB"]
    end
    
    %% Frontend connections
    UI <--> SimEngine
    UI <--> PortStore
    UI <--> CharStore
    UI <--> Events
    SimEngine <--> TradingSystem
    SimEngine <--> Events
    TradingSystem <--> PortStore
    Events <--> CharStore
    
    %% Backend hierarchy
    CEO -- "1. Strategic Planning<br>5. Decision Making" --> LLM
    CEO -- "2. Task Delegation" --> Manager
    CEO -- "3. Portfolio Queries" --> Portfolio
    
    Manager -- "Analysis Tasks" --> TechAnalysis
    Manager -- "Analysis Tasks" --> FundAnalysis
    Manager -- "Results Analysis" --> LLM
    
    %% Data sources
    TechAnalysis -- "Price Data" --> MarketData
    FundAnalysis -- "Financial Reports" --> MarketData
    Portfolio --> DB
    Manager --> DB
    
    %% API Communications
    UI -- "Trading Initiation<br>/api/trading/start" -.-> CEO
    UI -- "Portfolio Status<br>/api/portfolios" -.-> Portfolio
    UI -- "Analysis Status<br>/api/analysis" -.-> Manager
    
    %% Data flow descriptions
    CEO -- "4. Combined Analysis" --> Manager
    Manager -- "Fundamental Data" --> FundAnalysis
    Manager -- "Technical Data" --> TechAnalysis
    TechAnalysis -- "Price Predictions" --> Manager
    FundAnalysis -- "Valuation Models" --> Manager
    Portfolio -- "Position Data" --> CEO
    
    %% Component descriptions
    classDef frontend fill:#D6EAF8,stroke:#2E86C1,color:black
    classDef agent fill:#D5F5E3,stroke:#27AE60,color:black
    classDef external fill:#FCF3CF,stroke:#F1C40F,color:black
    
    class UI,SimEngine,TradingSystem,CharStore,PortStore,Events frontend
    class CEO,Manager,Portfolio,TechAnalysis,FundAnalysis agent
    class MarketData,LLM,DB external
```