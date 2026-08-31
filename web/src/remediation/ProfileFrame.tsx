import { PROFILE, PROFILE_NOTICE, censusComputed, type FolderSetProfile } from './profileData'

// The PROFILE frame (O59): what the export ACTUALLY says.
//
// The division this whole surface rests on — the machine reports what IS, the
// SME supplies what is NOT THERE. So nothing here is a recommendation, a
// score, or a judgement: every section is a census, and the findings live in
// their own frame because the profile asserts nothing about meaning.
//
// THE HONESTY RULES ARE THE FEATURE, inherited from O56/O58:
//   * a census the profile did not COMPUTE renders "not profiled" — never 0.
//     Zero is an answer; absence is not, and printing 0 for "we did not look"
//     is the kind of confident wrong number this module exists to remove.
//   * every count carries WHERE-USED. G68 built the censuses that way because
//     the SME's next question is always "which jobs?", and a distinct-value
//     list that cannot answer it sends them back to the XML.
//   * inferred facts say so. The dataset list is read off the sub-folder
//     ladder, which is a reading of the shape and not a declared fact.
//
// FIVE CENSUSES, NOT FOUR. O59's acceptance names four; census (e),
// INVOCATIONS, was merged into G68 from Idea-140 on 2026-08-19, eight days
// after O59 was raised. It is rendered because it exists and an SME reading a
// folder set wants it — omitting it to match older wording would be following
// the letter of an item against its own purpose.

const CARD = 'rounded-md border border-edge'
const HEAD =
  'border-b border-edge bg-panel-2 px-2.5 py-1.5 font-mono text-[11px] font-semibold text-muted'
const TH = 'border-b border-edge px-2.5 py-1.5 text-left font-semibold text-muted'
const TD = 'border-b border-edge-soft px-2.5 py-1.5 align-top text-text'

function Section({
  title,
  census,
  count,
  unit = 'row',
  children,
}: {
  title: string
  census: keyof FolderSetProfile
  count: number
  /** What the count counts. Shape is not a table, so "4 rows" would be a lie. */
  unit?: string
  children: React.ReactNode
}) {
  const computed = censusComputed(census)
  return (
    <section className={CARD}>
      <p className={HEAD}>
        {title}
        <span className="ml-2 font-sans font-normal">
          {!computed ? (
            <span className="text-yellow">not profiled</span>
          ) : count === 0 ? (
            'none found'
          ) : (
            `${count} ${unit}${count === 1 ? '' : 's'}`
          )}
        </span>
      </p>
      {!computed ? (
        <p className="px-2.5 py-2 text-[11px] text-muted">
          This census is not present in the profile artifact. That is not the same as an empty
          one — nothing looked, so nothing can be concluded.
        </p>
      ) : count === 0 ? (
        <p className="px-2.5 py-2 text-[11px] text-muted">The census ran and found nothing.</p>
      ) : (
        <div className="overflow-x-auto">{children}</div>
      )}
    </section>
  )
}

function Jobs({ jobs }: { jobs: string[] }) {
  return (
    <span className="font-mono text-[10px] text-muted" title={jobs.join(', ')}>
      {jobs.length} job{jobs.length === 1 ? '' : 's'}
      {jobs.length <= 2 ? ` — ${jobs.join(', ')}` : ''}
    </span>
  )
}

export default function ProfileFrame() {
  const p = PROFILE
  const shape = p.shape

  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
        {PROFILE_NOTICE}
      </p>
      <div className="min-h-0 flex-1 space-y-1.5 overflow-auto pr-0.5 text-xs">
        <p className="rounded border border-edge bg-panel-2 px-2.5 py-1.5 font-mono text-[11px] text-muted">
          source: <span className="text-text">{p.source}</span>
          <span className="ml-2 font-sans">{p.summary}</span>
        </p>

        {/* (a) SHAPE */}
        <Section title="Shape" census="shape" count={shape.jobs} unit="job">
          <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 px-2.5 py-2 text-[11px]">
            <dt className="text-muted">data centers</dt>
            <dd className="font-mono text-text">{shape.data_centers.join(', ') || '—'}</dd>
            <dt className="text-muted">folders</dt>
            <dd className="font-mono text-text">{shape.folders.join(', ')}</dd>
            <dt className="text-muted">sub-folders</dt>
            <dd className="font-mono text-text">{shape.subfolders.join(', ')}</dd>
            <dt className="text-muted">jobs by type</dt>
            <dd className="font-mono text-text">
              {Object.entries(shape.jobs_by_type)
                .map(([type, n]) => `${type}: ${n}`)
                .join('  ·  ')}
            </dd>
            <dt className="text-muted">datasets</dt>
            <dd className="font-mono text-text">
              {shape.datasets_inferred.join(', ')}
              <span className="ml-2 font-sans text-[10px] text-yellow">
                INFERRED from the sub-folder ladder — a reading of the shape, not a declared
                fact. The SME can correct it.
              </span>
            </dd>
          </dl>
        </Section>

        {/* (b) IDENTITY */}
        <Section title="Identity" census="identity" count={p.identity.length}>
          <table className="w-full border-collapse">
            <thead className="bg-panel-2">
              <tr>
                <th className={TH}>Fact</th>
                <th className={TH}>Value</th>
                <th className={TH}>Where used</th>
                <th className={TH}>Job types</th>
              </tr>
            </thead>
            <tbody>
              {p.identity.map((row) => (
                <tr key={`${row.fact}:${row.value}`}>
                  <td className={`${TD} font-mono text-[11px]`}>{row.fact}</td>
                  <td className={`${TD} font-mono text-[11px]`}>{row.value}</td>
                  <td className={TD}>
                    <Jobs jobs={row.jobs} />
                  </td>
                  {/* RUN_AS only. The FileWatcher-on-the-platform-account pattern
                      is the DESIGNED one; flat, it reads as "two accounts". */}
                  <td className={`${TD} font-mono text-[10px] text-muted`}>
                    {row.job_types.join(', ') || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        {/* (c) VARIABLES — census and defect state in ONE table */}
        <Section title="Variables" census="variables" count={p.variables.length}>
          <table className="w-full border-collapse">
            <thead className="bg-panel-2">
              <tr>
                <th className={TH}>Name</th>
                <th className={TH}>Scope</th>
                <th className={TH}>Declared in</th>
                <th className={TH}>Values</th>
                <th className={TH}>Refs</th>
                <th className={TH}>State</th>
              </tr>
            </thead>
            <tbody>
              {p.variables.map((row) => (
                <tr key={`${row.name}:${row.scope}:${row.containers.join(',')}`}>
                  <td className={`${TD} font-mono text-[11px]`}>{row.name}</td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>{row.scope}</td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>
                    {row.containers.join(', ')}
                  </td>
                  <td className={`${TD} tabular-nums`}>{row.distinct_values}</td>
                  <td className={`${TD} tabular-nums`}>{row.reference_count}</td>
                  {/* R30/R31 state INLINE: census and defect list are one table,
                      not two the reader has to join by hand. */}
                  <td className={TD}>
                    {row.unresolved && (
                      <span className="mr-1 font-mono text-[10px] text-[var(--status-fail-soft)]">
                        R30 unresolved
                      </span>
                    )}
                    {row.unreferenced && (
                      <span className="font-mono text-[10px] text-yellow">R31 unreferenced</span>
                    )}
                    {!row.unresolved && !row.unreferenced && (
                      <span className="text-[10px] text-muted">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        {/* (d) CONTACTS */}
        <Section title="Contacts" census="contacts" count={p.contacts.length}>
          <table className="w-full border-collapse">
            <thead className="bg-panel-2">
              <tr>
                <th className={TH}>Name</th>
                <th className={TH}>Value</th>
                <th className={TH}>Kind</th>
                <th className={TH}>Declared in</th>
                <th className={TH}>Use</th>
              </tr>
            </thead>
            <tbody>
              {p.contacts.map((row) => (
                <tr key={`${row.name}:${row.value}`}>
                  <td className={`${TD} font-mono text-[11px]`}>{row.name}</td>
                  <td className={`${TD} font-mono text-[11px]`}>{row.value}</td>
                  {/* Support tier and delay-notification consumer are different
                      audiences and MUST NOT be collapsed (guidelines §7.3). */}
                  <td className={`${TD} font-mono text-[10px] text-muted`}>{row.kind}</td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>
                    {row.containers.join(', ')}
                  </td>
                  <td className={TD}>
                    {row.documentation_only ? (
                      <span className="font-mono text-[10px] text-yellow">
                        documentation only — R40 deletes the block that would have used it
                      </span>
                    ) : (
                      <span className="text-[10px] text-muted">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        {/* (e) INVOCATIONS */}
        <Section title="Invocations" census="invocations" count={p.invocations.length}>
          <table className="w-full border-collapse">
            <thead className="bg-panel-2">
              <tr>
                <th className={TH}>Invoked</th>
                <th className={TH}>Type</th>
                <th className={TH}>Fan-out</th>
                <th className={TH}>Varies across the fan-out</th>
                <th className={TH}>Constant</th>
              </tr>
            </thead>
            <tbody>
              {p.invocations.map((row) => (
                <tr key={row.target}>
                  <td className={`${TD} font-mono text-[11px]`}>{row.target}</td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>
                    {row.invocation_type}
                  </td>
                  <td className={`${TD} tabular-nums`}>
                    {row.fan_out}
                    <span className="ml-1 block font-mono text-[10px] text-muted">
                      {row.fan_out > 1 ? 'shared wrapper' : 'one-to-one'}
                    </span>
                  </td>
                  {/* Identity-grade CANDIDATES. Which parameter is the token is
                      a lineage-gate ruling; this census informs it, never makes it. */}
                  <td className={`${TD} font-mono text-[10px]`}>
                    {row.varying_variables.join(', ') || '—'}
                  </td>
                  <td className={`${TD} font-mono text-[10px] text-muted`}>
                    {row.constant_variables.join(', ') || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="border-t border-edge-soft px-2.5 py-1.5 text-[10px] text-muted">
            A wrapper shared by many jobs means the PATH distinguishes nothing — the varying
            parameters are the identity-grade candidates. Fan-out 1 is reported for the same
            reason in reverse: it is the evidence that path identity IS sufficient for that
            kind. Which parameter is the token is a lineage-gate ruling; this census informs it
            and never makes it.
          </p>
        </Section>
      </div>
    </div>
  )
}
