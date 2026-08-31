import { PROFILE, PROFILE_NOTICE } from './profileData'
import { groupFindings } from './findingClasses'

// The FINDINGS frame (O59): detect_all()'s output, grouped by rule id, with
// the two failure classes REPORTED APART.
//
// WHY THE SPLIT IS THE DESIGN AND NOT A FLOURISH. Name drift produces
// SILENCE — the variable misses the fact registry, no row is written, and the
// lineage is simply absent. A value-contract breach produces a CONFIDENTLY
// WRONG row — the name resolves, so a fact IS written, carrying a false
// value. A page that ranks them together teaches the reader the wrong triage
// order: the silent one announces itself as a gap somebody eventually
// notices, and the wrong one never announces itself at all. The reasoning is
// detect.py's own, and `findingClasses.ts` holds the mapping.
//
// EVERY ROW CITES ITS RULE ID so the reader can reach the registry entry.
// The rule TEXT is deliberately not reproduced here: the registry lives in
// internal/ and its entries name real systems, so the console shows the id
// and the detector's own mechanism-only message, and the reader opens the
// registry for the rest.
//
// NOTHING HERE IS RATIFIED. `ratified` is false on every finding by
// construction — registry ratification is gate territory (M1) — so the frame
// shows the flag rather than hiding it, and no row is presented as a change
// anybody is cleared to make.

const TH = 'border-b border-edge px-2.5 py-1.5 text-left font-semibold text-muted'
const TD = 'border-b border-edge-soft px-2.5 py-1.5 align-top text-text'

const SEVERITY_TOKEN: Record<string, string> = {
  'must-fix': '--status-fail-soft',
  'should-fix': '--yellow',
  advisory: '--muted',
}

function Severity({ severity }: { severity: string }) {
  const token = SEVERITY_TOKEN[severity] ?? '--muted'
  return (
    <span
      className="rounded-full border px-1.5 py-0.5 font-mono text-[10px] font-semibold"
      style={{
        borderColor: `var(${token})`,
        color: `var(${token})`,
        background: `color-mix(in srgb, var(${token}) 10%, transparent)`,
      }}
    >
      {severity}
    </span>
  )
}

export default function StandardsFindings() {
  const groups = groupFindings(PROFILE.findings)

  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <p className="shrink-0 rounded border border-yellow/50 bg-yellow/10 px-2 py-1 font-mono text-[10px] text-yellow">
        {PROFILE_NOTICE}
      </p>
      <p className="shrink-0 rounded border border-edge bg-panel-2 px-2.5 py-1.5 text-[11px] text-muted">
        <span className="font-mono font-semibold text-text">{PROFILE.findings.length}</span>{' '}
        findings from <span className="font-mono">detect_all()</span>, riding alongside the
        census — the profile asserts nothing about meaning, so the defect list stays the
        detector&rsquo;s output and is carried, never restated. Nothing here is ratified, and
        nothing on this page writes XML or a graph.
      </p>

      <div className="min-h-0 flex-1 space-y-1.5 overflow-auto pr-0.5 text-xs">
        {groups.map((group) => (
          <section key={group.id} className="rounded-md border border-edge">
            <div
              className="border-b border-edge px-2.5 py-1.5"
              style={{ background: `color-mix(in srgb, var(${group.token}) 7%, transparent)` }}
            >
              <p className="font-mono text-[11px] font-semibold" style={{ color: `var(${group.token})` }}>
                {group.title}
                <span className="ml-2 tabular-nums">
                  {group.count} finding{group.count === 1 ? '' : 's'}
                </span>
              </p>
              {/* The effect on the downstream row IS the reason for the split,
                  so it is stated on the section rather than in a legend. */}
              <p className="mt-0.5 text-[10px] leading-snug text-muted">{group.effect}</p>
            </div>

            {group.count === 0 ? (
              <p className="px-2.5 py-2 text-[11px] text-muted">
                None in this folder set. The class is shown anyway — a section that disappears
                when it is empty reads as &ldquo;this page does not check for that&rdquo;.
              </p>
            ) : (
              group.rules.map((rule) => (
                <div key={rule.ruleId} className="border-b border-edge-soft last:border-b-0">
                  <p className="flex items-center gap-2 bg-panel-2 px-2.5 py-1">
                    <span className="font-mono text-[11px] font-semibold text-text">
                      {rule.ruleId}
                    </span>
                    <Severity severity={rule.severity} />
                    <span className="tabular-nums text-[10px] text-muted">
                      {rule.findings.length} hit{rule.findings.length === 1 ? '' : 's'}
                    </span>
                    <span className="text-[10px] text-muted">
                      · see the standards-rules registry entry for {rule.ruleId}
                    </span>
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr>
                          <th className={TH}>Target</th>
                          <th className={TH}>Severity</th>
                          <th className={TH}>What the detector found</th>
                          <th className={TH}>Ratified</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rule.findings.map((finding, i) => (
                          <tr key={`${finding.target}:${i}`}>
                            <td className={`${TD} font-mono text-[11px]`}>{finding.target}</td>
                            <td className={TD}>
                              <Severity severity={finding.severity} />
                            </td>
                            <td className={`${TD} text-[11px] leading-snug`}>{finding.message}</td>
                            <td className={`${TD} font-mono text-[10px] text-muted`}>
                              {finding.ratified ? 'yes' : 'no — gate territory (M1)'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))
            )}
          </section>
        ))}
      </div>
    </div>
  )
}
