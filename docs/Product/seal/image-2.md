graph TD
    A["🟧 Alpha Application"]

    A -->|Part of| B["🟦 Global Reporting Data Store\n(Application Module)"]
    A -->|Part of| C["🟦 Operational Data Store\n(Application Module)"]
    A --- D["🟦 Others\n(Application Module)"]

    B -->|Used as| E["🟩 Alpha Global Reporting Data Store\n(Deployment Module)"]
    C -->|Used as| F["🟩 Alpha NA ODS\n(Deployment Module)"]
    C -->|Used as| G["🟩 Alpha APAC ODS\n(Deployment Module)"]
    D --- H["🟩 Others\n(Deployment Module)"]

    E -->|Used by| I["🟪 Alpha Deployment NA\n(App System Logical Deployment)"]
    F -->|Used by| I
    G -->|Used by| J["🟪 Alpha Deployment APAC\n(App System Logical Deployment)"]

    style A fill:#FFA500,color:#000,stroke:#cc8400
    style B fill:#1E6FBF,color:#fff,stroke:#155a9e
    style C fill:#1E6FBF,color:#fff,stroke:#155a9e
    style D fill:#1E6FBF,color:#fff,stroke:#155a9e
    style E fill:#1a6e1a,color:#fff,stroke:#145214
    style F fill:#1a6e1a,color:#fff,stroke:#145214
    style G fill:#1a6e1a,color:#fff,stroke:#145214
    style H fill:#1a6e1a,color:#fff,stroke:#145214
    style I fill:#6a0dad,color:#fff,stroke:#4b0082
    style J fill:#6a0dad,color:#fff,stroke:#4b0082