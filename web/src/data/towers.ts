// SYNTHESIZED DATA — no real systems, SEALs, folder/job names, or org data
// (publish boundary). Verbatim port of the UI-WIP dark-landing mockup's TOWERS
// dataset (commit dd270b2): four CTO towers, each with an illustrative lineage
// query, graph, schema, and anonymized row preview.

export type TowerKey = 'home' | 'auto' | 'cards' | 'shared'

export interface GraphNode {
  x: number
  y: number
  label: string
  sub: string
  c: string
}

export interface GraphSpec {
  nodes: readonly GraphNode[]
  edges: readonly (readonly [number, number, string])[]
}

export interface TowerDef {
  key: TowerKey
  title: string
  color: string
  stats: readonly (readonly [string, string])[]
  schemaName: string
  schema: readonly (readonly [string, string])[]
  previewName: string
  prevCols: readonly string[]
  preview: readonly (readonly string[])[]
  /** cypher with kw/lbl/rel/str span markup — static in-repo literal, rendered via innerHTML */
  cypherHtml: string
  graph: GraphSpec
}

export const TOWERS: Record<TowerKey, TowerDef> = {
  home: {
    key: 'home',
    title: 'Home Lending',
    color: '#4D8BE0',
    stats: [['12', 'Products'], ['42', 'Teams']],
    schemaName: 'HomeLending_Data_Model',
    schema: [['Id', 'int'], ['Applicant', 'string'], ['Anonymized_Loan', 'string'], ['Stage', 'string'], ['App_Dt', 'date']],
    previewName: 'Anonymized Applications',
    prevCols: ['Id', 'Applicant', 'Anonymized_Loan'],
    preview: [['501', 'M. Rivera', 'HL0… ****'], ['502', 'T. Chen', 'HL0… ****'], ['503', 'A. Osei', 'illustrative …']],
    cypherHtml: `<span class="kw">MATCH</span> (t:<span class="lbl">Tower</span> {name: <span class="str">'Home Lending'</span>})
      -[:<span class="rel">RUNS</span>]-&gt;(j:<span class="lbl">EtlJob</span> {engine: <span class="str">'Informatica'</span>})
      -[:<span class="rel">WRITES</span>]-&gt;(d:<span class="lbl">Dataset</span>)
      -[:<span class="rel">LANDS_IN</span>]-&gt;(s:<span class="lbl">S3Stage</span> {name: <span class="str">'stg_mortgage'</span>})
      -[:<span class="rel">LOADS</span>]-&gt;(w:<span class="lbl">Warehouse</span> {name: <span class="str">'Snowflake_DW'</span>})
<span class="kw">OPTIONAL MATCH</span> (j)-[:<span class="rel">SCHEDULED_BY</span>]-&gt;(cm:<span class="lbl">ControlMJob</span>)
<span class="kw">RETURN</span> t, j, d, s, w, cm
<span class="kw">ORDER BY</span> cm.medianStartTime`,
    graph: {
      nodes: [
        { x: 75, y: 150, label: 'Home Lending', sub: 'Tower', c: '#C8202E' },
        { x: 210, y: 70, label: 'm_app_approval', sub: 'EtlJob', c: '#D9B831' },
        { x: 335, y: 150, label: 'app_pipeline', sub: 'Dataset', c: '#4D8BE0' },
        { x: 460, y: 70, label: 'stg_mortgage', sub: 'S3Stage', c: '#3AAE6B' },
        { x: 552, y: 150, label: 'Snowflake_DW', sub: 'Warehouse', c: '#2AB3A6' },
        { x: 210, y: 240, label: 'HL_DLY_LOAD', sub: 'ControlMJob', c: '#9B6BD4' },
      ],
      edges: [[0, 1, 'RUNS'], [1, 2, 'WRITES'], [2, 3, 'LANDS_IN'], [3, 4, 'LOADS'], [1, 5, 'SCHEDULED_BY']],
    },
  },

  auto: {
    key: 'auto',
    title: 'Auto',
    color: '#2AB3A6',
    stats: [['9', 'Products'], ['31', 'Teams']],
    schemaName: 'Auto_Data_Model',
    schema: [['Id', 'int'], ['Dealer', 'string'], ['Anonymized_VIN', 'string'], ['Inv_Status', 'string'], ['Lot_Dt', 'date']],
    previewName: 'Anonymized Inventory',
    prevCols: ['Id', 'Dealer', 'Anonymized_VIN'],
    preview: [['901', 'Dealer NW-04', 'V17… ****'], ['902', 'Dealer SE-11', 'V17… ****'], ['903', 'Dealer MW-02', 'illustrative …']],
    cypherHtml: `<span class="kw">MATCH</span> (t:<span class="lbl">Tower</span> {name: <span class="str">'Auto'</span>})
      -[:<span class="rel">RUNS</span>]-&gt;(j:<span class="lbl">EtlJob</span> {engine: <span class="str">'PySpark'</span>})
      -[:<span class="rel">WRITES</span>]-&gt;(d:<span class="lbl">Dataset</span>)
      -[:<span class="rel">LANDS_IN</span>]-&gt;(s:<span class="lbl">S3Stage</span> {name: <span class="str">'stg_auto'</span>})
      -[:<span class="rel">LOADS</span>]-&gt;(w:<span class="lbl">Warehouse</span> {name: <span class="str">'Snowflake_DW'</span>})
<span class="kw">OPTIONAL MATCH</span> (d)&lt;-[:<span class="rel">SOURCES</span>]-(lg:<span class="lbl">Dataset</span> {origin: <span class="str">'Cards legacy'</span>})
<span class="kw">RETURN</span> t, j, d, s, w, lg`,
    graph: {
      nodes: [
        { x: 75, y: 150, label: 'Auto', sub: 'Tower', c: '#C8202E' },
        { x: 215, y: 70, label: 'prod_inventory', sub: 'EtlJob', c: '#D9B831' },
        { x: 340, y: 150, label: 'inv_feed', sub: 'Dataset', c: '#4D8BE0' },
        { x: 462, y: 70, label: 'stg_auto', sub: 'S3Stage', c: '#3AAE6B' },
        { x: 552, y: 150, label: 'Snowflake_DW', sub: 'Warehouse', c: '#2AB3A6' },
        { x: 340, y: 245, label: 'cards_legacy', sub: 'Dataset', c: '#4D8BE0' },
      ],
      edges: [[0, 1, 'RUNS'], [1, 2, 'WRITES'], [2, 3, 'LANDS_IN'], [3, 4, 'LOADS'], [5, 2, 'SOURCES']],
    },
  },

  cards: {
    key: 'cards',
    title: 'Credit Cards',
    color: '#3AAE6B',
    stats: [['8', 'Products'], ['27', 'Teams']],
    schemaName: 'Cards_Data_Model',
    schema: [['Id', 'int'], ['Name', 'string'], ['Anonymized_Card', 'string'], ['Account_Status', 'string'], ['Open_Dt', 'date']],
    previewName: 'Anonymized Cardholders',
    prevCols: ['Id', 'Name', 'Anonymized_Card'],
    preview: [['123', 'John S.', 'S00… ****'], ['124', 'John N.', 'S00… ****'], ['125', 'Eava R.', 'illustrative …']],
    cypherHtml: `<span class="kw">MATCH</span> (t:<span class="lbl">Tower</span> {name: <span class="str">'Credit Cards'</span>})
      -[:<span class="rel">RUNS</span>]-&gt;(j:<span class="lbl">EtlJob</span> {engine: <span class="str">'AbInitio'</span>})
      -[:<span class="rel">WRITES</span>]-&gt;(d:<span class="lbl">Dataset</span>)
      -[:<span class="rel">LANDS_IN</span>]-&gt;(s:<span class="lbl">S3Stage</span> {name: <span class="str">'stg_cards'</span>})
      -[:<span class="rel">LOADS</span>]-&gt;(w:<span class="lbl">Warehouse</span> {name: <span class="str">'Snowflake_DW'</span>})
<span class="kw">OPTIONAL MATCH</span> (w)&lt;-[:<span class="rel">READS</span>]-(x:<span class="lbl">Tower</span>)
<span class="kw">WHERE</span> x.name &lt;&gt; t.name
<span class="kw">RETURN</span> t, j, d, s, w, x`,
    graph: {
      nodes: [
        { x: 75, y: 150, label: 'Credit Cards', sub: 'Tower', c: '#C8202E' },
        { x: 200, y: 70, label: 'Txn_ETL', sub: 'EtlJob', c: '#D9B831' },
        { x: 325, y: 150, label: 'txn_daily', sub: 'Dataset', c: '#4D8BE0' },
        { x: 450, y: 70, label: 'stg_cards', sub: 'S3Stage', c: '#3AAE6B' },
        { x: 548, y: 150, label: 'Snowflake_DW', sub: 'Warehouse', c: '#2AB3A6' },
        { x: 450, y: 240, label: 'Auto', sub: 'Tower', c: '#C8202E' },
      ],
      edges: [[0, 1, 'RUNS'], [1, 2, 'WRITES'], [2, 3, 'LANDS_IN'], [3, 4, 'LOADS'], [5, 4, 'READS']],
    },
  },

  shared: {
    key: 'shared',
    title: 'Shared Services',
    color: '#D9B831',
    stats: [['6', 'Platforms'], ['19', 'Teams']],
    schemaName: 'SharedSvc_Registry_Model',
    schema: [['Id', 'int'], ['Platform', 'string'], ['Owner_Team', 'string'], ['Consumers', 'int'], ['Onboard_Dt', 'date']],
    previewName: 'Platform Registry',
    prevCols: ['Id', 'Platform', 'Consumers'],
    preview: [['71', 'Batch Scheduling Registry', '14'], ['72', 'Vendor Icon Registry', '9'], ['73', 'Lending Knowledge Graph', 'illustrative …']],
    cypherHtml: `<span class="kw">MATCH</span> (t:<span class="lbl">Tower</span> {name: <span class="str">'Shared Services'</span>})
      -[:<span class="rel">OWNS</span>]-&gt;(p:<span class="lbl">Platform</span>)
      &lt;-[:<span class="rel">CONSUMES</span>]-(x:<span class="lbl">Tower</span>)
<span class="kw">OPTIONAL MATCH</span> (p)-[:<span class="rel">CATALOGS</span>]-&gt;(j:<span class="lbl">ControlMJob</span>)
<span class="kw">RETURN</span> t, p, x,
       count(j) <span class="kw">AS</span> jobsCataloged
<span class="kw">ORDER BY</span> jobsCataloged <span class="kw">DESC</span>`,
    graph: {
      nodes: [
        { x: 80, y: 150, label: 'Shared Services', sub: 'Tower', c: '#C8202E' },
        { x: 250, y: 70, label: 'Sched Registry', sub: 'Platform', c: '#D9B831' },
        { x: 250, y: 230, label: 'Knowledge Graph', sub: 'Platform', c: '#D9B831' },
        { x: 430, y: 70, label: 'Home Lending', sub: 'Tower', c: '#C8202E' },
        { x: 430, y: 230, label: 'Auto', sub: 'Tower', c: '#C8202E' },
        { x: 545, y: 150, label: 'HL_DLY_LOAD', sub: 'ControlMJob', c: '#9B6BD4' },
      ],
      edges: [[0, 1, 'OWNS'], [0, 2, 'OWNS'], [3, 1, 'CONSUMES'], [4, 2, 'CONSUMES'], [1, 5, 'CATALOGS']],
    },
  },
}

export const TOWER_KEYS = Object.keys(TOWERS) as readonly TowerKey[]

export function isTowerKey(key: string): key is TowerKey {
  return key in TOWERS
}

// Inter-tower dependency matrix (mockup's table, tidied — all synthesized).
export const DEPENDENCY_MATRIX = {
  cols: ['Tower', 'Shared S3 Buckets', 'Snowflake', 'Notes'],
  rows: [
    ['Auto', 'stg_auto · reads S3_Cards', 'Snowflake_DW', 'uses data from the Cards legacy systems'],
    ['Credit Cards', 'stg_cards (shared to Auto)', 'Snowflake_DW', '—'],
    ['Home Lending', 'stg_mortgage', 'Snowflake_DW', '—'],
    ['Shared Services', '—', '—', 'owns the platform registries'],
  ],
} as const

// My Apps rollup rendered with the same graph renderer (mirrors the mockup's
// ROLLS_UP_TO SVG: three apps -> the Home Lending Technology CTO tower).
export const MY_APPS_ROLLUP: GraphSpec = {
  nodes: [
    { x: 310, y: 50, label: 'Home Lending Technology', sub: 'CTO Tower · ccb-twr-hl', c: '#4D8BE0' },
    { x: 100, y: 210, label: 'Origination Workbench', sub: 'ccb-hl-app-01', c: '#3AAE6B' },
    { x: 310, y: 230, label: 'Servicing Core', sub: 'ccb-hl-app-02', c: '#4D8BE0' },
    { x: 520, y: 210, label: 'Portfolio Analytics', sub: 'ccb-hl-app-03', c: '#C8202E' },
  ],
  edges: [[1, 0, 'ROLLS_UP_TO'], [2, 0, 'ROLLS_UP_TO'], [3, 0, 'ROLLS_UP_TO']],
}
