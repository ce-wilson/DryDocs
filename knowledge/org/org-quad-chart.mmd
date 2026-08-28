graph TB
    %% Styling Classes
    classDef layerFill fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,font-weight:bold;
    classDef da fill:#fde8e8,stroke:#9b1c1c,stroke-width:2px;
    classDef dce fill:#fffaf0,stroke:#dd6b20,stroke-width:2px;
    classDef prod fill:#f0fdf4,stroke:#166534,stroke-width:2px;
    classDef tech fill:#eff6ff,stroke:#1d4ed8,stroke-width:2px;
    classDef grayNode fill:#f8fafc,stroke:#64748b,stroke-dasharray: 5 5;

    %% Subgraph Layer Structure
    subgraph LAYER1 [ORGANIZATION LAYER]
        CDAO[Chief Data & Analytics Officer]:::da
        CDO[Chief Design Officer]:::dce
        CIO[Chief Information Officer]:::tech
    end
    style LAYER1 fill:#fafafa,stroke:#334155,stroke-width:2px;

    subgraph LAYER2 [PORTFOLIO LAYER]
        HDA[Head of D&A]:::da
        HDCE[Head of DCE]:::dce
        HPROD[Head of Product]:::prod
        HTECH[Head of Tech]:::tech

        %% Portfolio Deep Tiers
        HR[Head of Research]:::dce
        HD[Head of Design]:::dce
        HC[Head of Content]:::dce
        DMOP[DMO Partner]:::dce
        
        LOBL[LOB / Functional Leaders]:::prod
        PPO[Product Portfolio Operation Lead]:::prod
        PPOS[PPO Support]:::prod
        
        HSRE[Head of Site Reliability Engineering]:::tech
    end
    style LAYER2 fill:#f8fafc,stroke:#334155,stroke-width:2px;

    subgraph LAYER3 [PRODUCT LAYER]
        PLDO[Portfolio Lead Data Owner]:::da
        DO[Data Owner]:::da
        ADO[Area Data Owner]:::da

        DP[Design Partner]:::dce
        RL[Research Lead]:::dce
        DL[Design Lead]:::dce
        CL[Content Lead]:::dce
        DMO[DMO]:::dce

        PO[Product Owner / Area PO]:::prod
        PDL[Product Delivery Lead]:::prod
        FS[Functional Support]:::prod
        PCAB[Product Cabinet]:::prod
        PA[Product Analysts]:::prod
        
        subgraph PDT [Product Delivery Tracking]
            PPM[Process / Project / Program Mgmt]:::prod
            TRM[Testing & Release Manager]:::prod
            IDM[Intake & Dependency Mgmt]:::prod
        end

        TP[Tech Partner]:::tech
        SRED[Site Reliability Engineering Director]:::tech
        ATP[Area Tech Partner]:::tech
        PE[Principal Engineer]:::tech
        PA_ARCH[Product Architect]:::tech
        SEM[Software Engineering Manager]:::tech
        
        subgraph ARCH [Arch Org Model]
            HA[Head of Architecture]:::grayNode
        end
    end
    style LAYER3 fill:#f1f5f9,stroke:#334155,stroke-width:2px;

    subgraph LAYER4 [TEAM / EXECUTION LAYER]
        DAT[Data & Analytics Support Teams]:::da
        IO[Information Owner]:::da

        ER[Experience Researchers]:::dce
        EDS[Experience Designers]:::dce
        CDS[Content Designers]:::dce

        PAL[Product Agility Leads / Agility Leads]:::prod

        SRE[Site Reliability Engineer]:::tech
        SWE[Software Engineer Teams<br>1-2 Teams of 5-8 Engineers]:::tech
    end
    style LAYER4 fill:#e2e8f0,stroke:#334155,stroke-width:2px;

    %% Structural Ancestry Lineage Connections
    CDAO --> HDA
    CDO --> HDCE
    CIO --> HTECH

    %% Portfolio Relationships
    HDCE --> HR & HD & HC & DMOP
    HPROD --> LOBL & PPO
    PPO --> PPOS
    HTECH --> HSRE

    %% Product Relationships
    HDA --> PLDO
    PLDO --> DO --> ADO
    
    HD & HC & DMOP --> DP
    DP --> RL & DL & CL & DMO
    
    LOBL & PPOS -.-> PO
    HPROD --> PO
    PO --> PDL & FS & PCAB & PA
    PDL --> PDT
    
    HSRE --> SRED
    HTECH --> TP
    TP --> SRED & ATP & PE & PA_ARCH
    ATP --> SEM
    HTECH -.-> ARCH

    %% Execution Mappings
    ADO --> DAT
    DAT --> IO
    RL --> ER
    DL --> EDS
    CL --> CDS
    
    PCAB --> PAL
    SEM --> SWE
    SRED --> SRE