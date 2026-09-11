import { useEffect, useMemo, useState, type ChangeEvent, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Banner,
  BannerContent,
  Button,
  Card,
  FlowLayout,
  Input,
  SaltProviderNext,
  StackLayout,
  StatusIndicator,
  Tab,
  TabBar,
  TabList,
  TabPanel,
  Tabs,
  TabTrigger,
  Table,
  TableContainer,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Tag,
  Text,
  ToggleButton,
  ToggleButtonGroup,
  type Density,
  type ValidationStatus,
} from '@salt-ds/core'
import { ArrowDownIcon, ArrowUpIcon, DownloadIcon, SearchIcon } from '@salt-ds/icons'
import '@salt-ds/theme/index.css'
import '@salt-ds/theme/css/theme-next.css'
import '@fontsource/open-sans/400.css'
import '@fontsource/open-sans/600.css'
import '@fontsource/open-sans/700.css'
import '@fontsource/pt-mono/400.css'
import './SaltPocRoute.css'
import LoadMapRoute from './LoadMapRoute'
import ModuleToolbar from '../layout/ModuleToolbar'
import ResizableSplit from '../components/ui/ResizableSplit'
import { MODULES } from '../modules/registry'
import {
  AD_HOC_COMMANDS,
  DEFECT_COUNT,
  DOC_CORPUS_COUNT,
  KINDS,
  MAP_ENTRIES_WITHOUT_SOURCE,
  RETIRED,
  SEQUENCE,
  SOURCELESS_LOADERS,
  SOURCES,
  STEPS_WITH_UNCOMMITTED_INPUTS,
  SYSTEMS,
  UNCHAINED_LOADERS,
  WIRING_STATES,
  ledgerPath,
  ledgerState,
  pipelineReach,
  wiringCensus,
  wiringState,
  type LoadMapSource,
} from '../loadmap/loadMapModel'
import {
  download,
  toCsv,
  useTableControls,
  useTableView,
  type RowGroup,
  type SortState,
} from '../components/ui/tableControls'

// Idea-192 PoC: /load-map with Salt DS leaf components; findings in docs/design/ui-exploration/salt-ds-poc.md.
// Tailwind spacing sits on plain divs only: Salt's CSS is unlayered, so it overrides utility padding/margin on its own components.

type SourceViewRow = LoadMapSource & { taxonomy: string }
type Skin = 'current' | 'salt' | 'salt-branded'

const loadMapModule = MODULES.find((m) => m.id === 'loadmap')!

const SKINS: readonly { id: Skin; label: string }[] = [
  { id: 'current', label: 'Current (Tailwind + ReUI)' },
  { id: 'salt', label: 'Salt, as shipped' },
  { id: 'salt-branded', label: 'Salt + DryDocs tokens' },
]
const DENSITIES: readonly Density[] = ['high', 'medium', 'low', 'touch']

// Mirrors LoadMapRoute's module-local column table.
const SOURCE_COLUMNS: readonly { label: string; key: string | null }[] = [
  { label: 'Source id', key: 'id' },
  { label: 'System', key: 'system' },
  { label: 'Origin', key: 'origin' },
  { label: 'Kind', key: 'kind' },
  { label: 'Authority', key: 'authority' },
  { label: 'Classification', key: 'classification' },
  { label: 'Confirmed', key: 'confirmed' },
  { label: 'Wiring', key: null },
  { label: 'Ledger', key: null },
  { label: 'Taxonomy', key: 'taxonomy' },
  { label: 'Pipeline reach', key: null },
  { label: 'Loaders', key: null },
]
const SOURCE_SEARCH_KEYS = ['id', 'system', 'origin', 'kind', 'authority', 'classification', 'taxonomy'] as const

// ui-conventions.md section 1 tokens onto Salt's four statuses; --muted has no Salt status.
const STATUS_FOR_TOKEN: Partial<Record<string, ValidationStatus>> = {
  '--green': 'success',
  '--yellow': 'warning',
  '--blue-br': 'info',
}

function useConsoleIsDark(): boolean {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))
  useEffect(() => {
    const root = document.documentElement
    const obs = new MutationObserver(() => setDark(root.classList.contains('dark')))
    obs.observe(root, { attributes: true, attributeFilter: ['class'] })
    return () => obs.disconnect()
  }, [])
  return dark
}

export default function SaltPocRoute() {
  const [params, setParams] = useSearchParams()
  const skin = SKINS.find((s) => s.id === params.get('skin'))?.id ?? 'salt'
  const density = DENSITIES.find((d) => d === params.get('density')) ?? 'high'
  const dark = useConsoleIsDark()

  function setParam(key: string, value: string) {
    const next = new URLSearchParams(params)
    next.set(key, value)
    setParams(next, { replace: true })
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 flex-wrap items-center gap-2 border-b border-edge bg-panel-2 px-4 py-1.5 text-xs text-muted">
        <span className="font-semibold text-text">Idea-192 PoC</span>
        <span className="text-faint">skin:</span>
        {SKINS.map((s) => (
          <button
            key={s.id}
            type="button"
            aria-pressed={skin === s.id}
            onClick={() => setParam('skin', s.id)}
            className={
              'rounded border px-2 py-0.5 text-[11px] ' +
              (skin === s.id ? 'border-blue-bright bg-panel text-text' : 'border-edge text-muted hover:text-text')
            }
          >
            {s.label}
          </button>
        ))}
        {skin !== 'current' && (
          <label className="ml-2 flex items-center gap-1">
            <span className="text-faint">density:</span>
            <select value={density} onChange={(e) => setParam('density', e.target.value)} className="text-[11px]">
              {DENSITIES.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>
        )}
        <span className="ml-auto text-faint">same data and table hooks in every skin; mode follows the console theme</span>
      </div>
      <div className="min-h-0 flex-1">
        {skin === 'current' ? (
          <LoadMapRoute />
        ) : (
          <div className="salt-poc-host h-full">
            {/* scope, not the root default: a root provider re-themes <html> and so the whole console */}
            <SaltProviderNext
              applyClassesTo="scope"
              mode={dark ? 'dark' : 'light'}
              density={density}
              corner={skin === 'salt-branded' ? 'rounded' : 'sharp'}
            >
              <div className={'h-full' + (skin === 'salt-branded' ? ' salt-poc-branded' : '')}>
                <SaltLoadMap />
              </div>
            </SaltProviderNext>
          </div>
        )}
      </div>
    </div>
  )
}

function SaltLoadMap() {
  const [kind, setKind] = useState<string | null>(null)
  const [tab, setTab] = useState<string>(loadMapModule.tabs[0])

  const shown: LoadMapSource[] = useMemo(() => (kind ? SOURCES.filter((s) => s.kind === kind) : SOURCES), [kind])
  const ctl = useTableControls()
  const decorated = useMemo(() => shown.map((s) => ({ ...s, taxonomy: s.taxonomy_captures.join(', ') })), [shown])
  const view = useTableView(decorated, {
    filter: ctl.filter,
    searchKeys: SOURCE_SEARCH_KEYS,
    sort: ctl.sort,
    groupKey: ctl.grouped ? 'system' : null,
  })

  const tiles = [
    { value: String(SOURCES.length), label: 'sources' },
    { value: String(SYSTEMS.length), label: 'systems' },
    { value: String(SEQUENCE.length), label: 'sequence steps' },
    { value: String(RETIRED.length), label: 'retired ids' },
    { value: String(AD_HOC_COMMANDS.length), label: 'ad-hoc commands' },
    { value: String(DEFECT_COUNT), label: 'declared defects' },
  ]

  const graphPane = (
    <div className="h-full min-h-0 p-3">
      <StackLayout gap={1} className="h-full min-h-0">
        <Banner status="info">
          <BannerContent>
            <strong>Declared, not observed.</strong> Every row comes from the registries via the generated{' '}
            <code>load-map.json</code>. Whether a load actually ran is /loads; the {DOC_CORPUS_COUNT} doc-corpus sources
            are rendered by /software.
          </BannerContent>
        </Banner>
        <FlowLayout gap={1}>
          {tiles.map((t) => (
            <Card key={t.label} variant="secondary" className="salt-poc-tile">
              <Text styleAs="display3">{t.value}</Text>
              <Text styleAs="label" color="secondary">
                {t.label}
              </Text>
            </Card>
          ))}
        </FlowLayout>
        <Card className="min-h-0 flex-1 overflow-auto">
          <StackLayout gap={1}>
            <Text styleAs="label" color="secondary">
              Canonical load sequence
            </Text>
            <FlowLayout gap={0.5} align="center">
              {SEQUENCE.map((step, i) => (
                <span key={`${step.command}-${i}`} className="inline-flex items-center gap-1">
                  <Tag title={step.note ?? undefined}>
                    {step.command}
                    {step.loaders.length ? ` ·${step.loaders.length}` : ''}
                  </Tag>
                  {i < SEQUENCE.length - 1 && <Text color="secondary">→</Text>}
                </span>
              ))}
            </FlowLayout>
            <Text styleAs="notation" color="secondary">
              Outside the sequence, run by hand and never scheduled: {AD_HOC_COMMANDS.join(', ')}
            </Text>
          </StackLayout>
        </Card>
      </StackLayout>
    </div>
  )

  function sourceRow(s: SourceViewRow) {
    const reach = pipelineReach(s)
    const path = ledgerPath(s.ledger)
    return (
      <TR key={s.id}>
        <TD className="salt-poc-mono">
          {s.id}
          {s.derived && (
            <Text as="span" color="secondary">
              {' '}
              · derived
            </Text>
          )}
        </TD>
        <TD>{s.system ?? '—'}</TD>
        <TD>{s.origin ?? '—'}</TD>
        <TD className="salt-poc-mono">{s.kind}</TD>
        <TD>{s.authority ?? '—'}</TD>
        <TD>{s.classification ?? '—'}</TD>
        <TD>{s.confirmed ? 'yes' : 'not yet'}</TD>
        <TD>
          <SaltWiring source={s} />
        </TD>
        <TD className="salt-poc-mono" title={path ?? undefined}>
          {ledgerState(s.ledger)}
        </TD>
        <TD className="salt-poc-mono">
          {s.taxonomy_captures.length ? s.taxonomy_captures.map((c) => <div key={String(c)}>{String(c)}</div>) : '—'}
        </TD>
        <TD>{reach.label}</TD>
        <TD className="salt-poc-mono">{s.loaders.map((l) => l.cli_name ?? l.name).join(', ') || '—'}</TD>
      </TR>
    )
  }

  function groupedRows(groups: RowGroup<SourceViewRow>[]) {
    return groups.flatMap((g) => [
      <TR key={`grp-${g.key}`}>
        <TD colSpan={SOURCE_COLUMNS.length} className="salt-poc-group">
          {g.label}{' '}
          <Text as="span" color="secondary">
            {g.rows.length}
          </Text>
        </TD>
      </TR>,
      ...g.rows.map(sourceRow),
    ])
  }

  const sourcesTab = (
    <StackLayout gap={1} className="h-full min-h-0">
      <FlowLayout gap={1} align="center">
        <Text styleAs="label" color="secondary">
          kind:
        </Text>
        <ToggleButtonGroup
          value={kind ?? 'all'}
          onChange={(e) => {
            const v = e.currentTarget.value
            setKind(v === 'all' ? null : v)
          }}
        >
          <ToggleButton value="all">all ({SOURCES.length})</ToggleButton>
          {KINDS.map((k) => (
            <ToggleButton key={k} value={k}>
              {k} ({SOURCES.filter((s) => s.kind === k).length})
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </FlowLayout>
      <SaltControlBar
        filter={ctl.filter}
        onFilter={ctl.setFilter}
        count={view.rows.length}
        total={shown.length}
        grouped={ctl.grouped}
        onToggleGroup={ctl.toggleGroup}
        onExport={() => download('load-map-sources.csv', toCsv(SOURCE_SEARCH_KEYS, view.rows))}
      />
      <SaltTable
        headerRow={
          <TR>
            {SOURCE_COLUMNS.map((c) => (
              <SaltSortableTH key={c.label} label={c.label} sortKey={c.key} sort={ctl.sort} onSort={ctl.cycleSort} />
            ))}
          </TR>
        }
      >
        {view.groups ? groupedRows(view.groups) : view.rows.map(sourceRow)}
      </SaltTable>
      <SaltWiringKey sources={view.rows} />
    </StackLayout>
  )

  const systemsTab = (
    <SaltTable headers={['System', 'Name', 'Layer', 'Classification', 'Sources', 'Taxonomy captures']}>
      {SYSTEMS.map((sys) => (
        <TR key={sys.id}>
          <TD className="salt-poc-mono">{sys.id}</TD>
          <TD>{sys.name}</TD>
          <TD>{sys.layer ?? '—'}</TD>
          <TD>{sys.classification ?? '—'}</TD>
          <TD>{SOURCES.filter((s) => s.system === sys.id).length}</TD>
          <TD>{sys.taxonomy_captures.length}</TD>
        </TR>
      ))}
    </SaltTable>
  )

  const sequenceTab = (
    <SaltTable headers={['#', 'Command', 'Mode', 'Profiles', 'Loaders', 'Note']}>
      {SEQUENCE.map((step, i) => (
        <TR key={`${step.command}-${i}`}>
          <TD>{i + 1}</TD>
          <TD className="salt-poc-mono">{step.command}</TD>
          <TD>{step.mode}</TD>
          <TD className="salt-poc-mono">{step.profiles.join(', ') || '—'}</TD>
          <TD className="salt-poc-mono">{step.loaders.join(', ') || '—'}</TD>
          <TD>{step.note ?? '—'}</TD>
        </TR>
      ))}
    </SaltTable>
  )

  const retiredTab = (
    <SaltTable headers={['Retired id', 'Replaced by', 'Why']}>
      {RETIRED.map((r) => (
        <TR key={r.id}>
          <TD className="salt-poc-mono">{r.id}</TD>
          <TD className="salt-poc-mono">{r.replaced_by.length ? r.replaced_by.join(', ') : '—'}</TD>
          <TD>{r.reason}</TD>
        </TR>
      ))}
    </SaltTable>
  )

  const defectsTab =
    DEFECT_COUNT === 0 ? (
      <SaltEmpty title="No declared defects" hint="All four generator-computed lists are empty in the committed load-map.json." />
    ) : (
      <StackLayout gap={2}>
        <SaltSection title={`Loaders with no registry source (${SOURCELESS_LOADERS.length})`}>
          <SaltTable fill={false} headers={['Loader', 'Class', 'Commands', 'Stated reason']}>
            {SOURCELESS_LOADERS.map((l) => (
              <TR key={l.name}>
                <TD className="salt-poc-mono">{l.name}</TD>
                <TD className="salt-poc-mono">{l.class}</TD>
                <TD className="salt-poc-mono">{l.commands.join(', ') || '—'}</TD>
                <TD>{l.reason}</TD>
              </TR>
            ))}
          </SaltTable>
        </SaltSection>
        <SaltSection title={`Map entries whose source is unregistered (${MAP_ENTRIES_WITHOUT_SOURCE.length})`}>
          <SaltTable fill={false} headers={['Entry', 'Status', 'Label', 'Names source', 'Exemption']}>
            {MAP_ENTRIES_WITHOUT_SOURCE.map((e) => (
              <TR key={e.id}>
                <TD className="salt-poc-mono">{e.id}</TD>
                <TD>{e.status}</TD>
                <TD className="salt-poc-mono">{e.label}</TD>
                <TD className="salt-poc-mono">{e.source}</TD>
                <TD>{e.exemption}</TD>
              </TR>
            ))}
          </SaltTable>
        </SaltSection>
        <SaltSection title={`Loaders in no chain, reachable only ad hoc (${UNCHAINED_LOADERS.length})`}>
          <SaltTable fill={false} headers={['CLI name', 'Class', 'Stated reason']}>
            {UNCHAINED_LOADERS.map((l) => (
              <TR key={l.name}>
                <TD className="salt-poc-mono">{l.name}</TD>
                <TD className="salt-poc-mono">{l.class}</TD>
                <TD>{l.reason ?? <strong>SILENT: no written reason; the suite fails on this row</strong>}</TD>
              </TR>
            ))}
          </SaltTable>
        </SaltSection>
        <SaltSection title={`Chain inputs not committed with the repo (${STEPS_WITH_UNCOMMITTED_INPUTS.length})`}>
          <SaltTable fill={false} headers={['Command', 'Step', 'File', 'Searched', 'Why']}>
            {STEPS_WITH_UNCOMMITTED_INPUTS.map((s) => (
              <TR key={`${s.step}-${s.file}`}>
                <TD className="salt-poc-mono">{s.command}</TD>
                <TD className="salt-poc-mono">{s.step}</TD>
                <TD className="salt-poc-mono">{s.file}</TD>
                <TD className="salt-poc-mono">{s.searched}</TD>
                <TD>{s.exemption ?? <strong>MISSING: a real run fails at preflight (G78)</strong>}</TD>
              </TR>
            ))}
          </SaltTable>
        </SaltSection>
      </StackLayout>
    )

  const byClassTab = (
    <Banner status="info">
      <BannerContent>
        Not reproduced in the PoC. This tab is nested Table, Text and StackLayout, which the other tabs already
        exercise, so it adds no component class to the comparison. Switch to the Current skin to see it.
      </BannerContent>
    </Banner>
  )

  const tabContent: Record<string, ReactNode> = {
    Sources: sourcesTab,
    'By class': byClassTab,
    Systems: systemsTab,
    'Load sequence': sequenceTab,
    'Retired ids': retiredTab,
    Defects: defectsTab,
  }

  const tabs = (
    <Tabs value={tab} onChange={(_e, v) => setTab(v)} className="flex h-full min-h-0 flex-col">
      <TabBar divider inset>
        <TabList aria-label="Data frames">
          {loadMapModule.tabs.map((label) => (
            <Tab key={label} value={label}>
              <TabTrigger>{label}</TabTrigger>
            </Tab>
          ))}
        </TabList>
      </TabBar>
      {loadMapModule.tabs.map((label) => (
        <TabPanel key={label} value={label} className="min-h-0 flex-1 overflow-auto p-3">
          {tabContent[label] ?? <SaltEmpty title={`${label}: no data source wired yet`} />}
        </TabPanel>
      ))}
    </Tabs>
  )

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ModuleToolbar
        crumbs={[{ label: 'Home', to: '/' }, { label: loadMapModule.label, to: '/load-map' }, { label: 'Salt PoC' }]}
      />
      <div className="px-4 pt-3">
        <FlowLayout justify="space-between" align="end">
          <StackLayout gap={0.5}>
            <Text as="h2" styleAs="h2" tabIndex={-1} data-view-heading className="outline-none">
              {loadMapModule.label}
            </Text>
            <Text color="secondary">
              {loadMapModule.tagline} · backs onto {loadMapModule.backsOnto}
            </Text>
          </StackLayout>
          <FlowLayout gap={1}>
            {['Layout', 'Fit', 'Refresh', 'Export'].map((label) => (
              <Button key={label} appearance="bordered" sentiment="neutral" disabled>
                {label}
              </Button>
            ))}
          </FlowLayout>
        </FlowLayout>
      </div>
      <div className="min-h-0 flex-1 p-4">
        <div className="salt-poc-frame h-full min-h-[420px] overflow-hidden">
          <ResizableSplit storageKey="drydocs.split.salt-poc.v1" top={graphPane} bottom={tabs} />
        </div>
      </div>
    </div>
  )
}

function SaltTable({
  headers,
  headerRow,
  children,
  fill = true,
}: {
  headers?: readonly string[]
  headerRow?: ReactNode
  children: ReactNode
  fill?: boolean
}) {
  return (
    <TableContainer className={fill ? 'salt-poc-table min-h-0 flex-1' : 'salt-poc-table'}>
      <Table zebra>
        <THead sticky>
          {headerRow ?? (
            <TR>
              {(headers ?? []).map((h) => (
                <TH key={h}>{h}</TH>
              ))}
            </TR>
          )}
        </THead>
        <TBody>{children}</TBody>
      </Table>
    </TableContainer>
  )
}

function SaltSortableTH({
  label,
  sortKey,
  sort,
  onSort,
}: {
  label: string
  sortKey: string | null
  sort: SortState
  onSort: (k: string) => void
}) {
  if (!sortKey) return <TH>{label}</TH>
  const active = sort?.key === sortKey
  return (
    <TH aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}>
      <Button appearance="transparent" sentiment="neutral" onClick={() => onSort(sortKey)} title={`Sort by ${label}`}>
        {label}
        {active && (sort.dir === 'asc' ? <ArrowUpIcon aria-hidden /> : <ArrowDownIcon aria-hidden />)}
      </Button>
    </TH>
  )
}

function SaltControlBar({
  filter,
  onFilter,
  count,
  total,
  grouped,
  onToggleGroup,
  onExport,
}: {
  filter: string
  onFilter: (v: string) => void
  count: number
  total: number
  grouped: boolean
  onToggleGroup: () => void
  onExport: () => void
}) {
  return (
    <FlowLayout gap={1} align="center">
      <Input
        value={filter}
        onChange={(e: ChangeEvent<HTMLInputElement>) => onFilter(e.target.value)}
        placeholder="filter rows"
        startAdornment={<SearchIcon aria-hidden />}
        inputProps={{ 'aria-label': 'Filter rows', type: 'search' }}
        style={{ width: '16rem' }}
      />
      <ToggleButton value="group" selected={grouped} onChange={() => onToggleGroup()}>
        group by system
      </ToggleButton>
      <Button appearance="bordered" sentiment="neutral" onClick={onExport}>
        <DownloadIcon aria-hidden /> export CSV
      </Button>
      <Text styleAs="label" color="secondary">
        {count === total ? `${total} rows` : `${count} of ${total} rows`}
      </Text>
    </FlowLayout>
  )
}

function SaltWiring({ source }: { source: LoadMapSource }) {
  const w = wiringState(source)
  const status = STATUS_FOR_TOKEN[w.token]
  return (
    <span className="inline-flex items-center gap-1" title={w.meaning}>
      {status ? <StatusIndicator status={status} /> : null}
      <Text as="span" styleAs="code" color={status ?? 'secondary'}>
        {w.label}
      </Text>
    </span>
  )
}

function SaltWiringKey({ sources }: { sources: readonly LoadMapSource[] }) {
  const census = wiringCensus(sources)
  return (
    <Card variant="tertiary">
      <StackLayout gap={0.5}>
        <Text styleAs="label">
          <strong>Wiring key</strong>: has a gate ruled this source&rsquo;s meaning, crossed with is a loader built that
          writes it.
        </Text>
        <FlowLayout gap={2}>
          {WIRING_STATES.map((s) => {
            const status = STATUS_FOR_TOKEN[s.token]
            return (
              <span key={s.id} className="inline-flex items-center gap-1">
                {status ? <StatusIndicator status={status} /> : null}
                <Text as="span" styleAs="code" color={status ?? 'secondary'}>
                  {s.label}
                </Text>
                <Text as="span" styleAs="notation" color="secondary">
                  {census[s.id]} · {s.meaning}
                </Text>
              </span>
            )
          })}
        </FlowLayout>
      </StackLayout>
    </Card>
  )
}

function SaltSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <StackLayout gap={0.5}>
      <Text styleAs="label" color="secondary">
        {title}
      </Text>
      {children}
    </StackLayout>
  )
}

function SaltEmpty({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="p-6 text-center">
      <StackLayout gap={0.5} align="center">
        <Text color="secondary">{title}</Text>
        {hint && (
          <Text styleAs="notation" color="secondary">
            {hint}
          </Text>
        )}
      </StackLayout>
    </div>
  )
}
