// SYNTHESIZED DATA — no real applications, SEALs, teams, towers, or SIDs
// (publish boundary). Values mirror the UI-WIP dark-landing mockup's My Apps
// panel (commit dd270b2) so the eventual design-pass port is a restyle, not a
// remodel: ServiceNow-derived app access rolling up to a CTO tower, dev teams
// sourced from PAT.

export type SnowPermission = 'Read' | 'Contribute' | 'Admin'

export interface DevTeam {
  name: string
  engineers: number
}

export interface Tower {
  id: string
  name: string
}

export interface MyApp {
  id: string
  name: string
  description: string
  snowPermission: SnowPermission
  team: DevTeam
  tower: Tower
}

const HOME_LENDING: Tower = { id: 'ccb-twr-hl', name: 'Home Lending Technology' }

const HOME_LENDING_APPS: readonly MyApp[] = [
  {
    id: 'ccb-hl-app-01',
    name: 'Origination Workbench',
    description: 'Loan application intake & underwriting',
    snowPermission: 'Contribute',
    team: { name: 'Team Keystone', engineers: 8 },
    tower: HOME_LENDING,
  },
  {
    id: 'ccb-hl-app-02',
    name: 'Servicing Core',
    description: 'Payments, escrow & loss mitigation',
    snowPermission: 'Read',
    team: { name: 'Team Gable', engineers: 12 },
    tower: HOME_LENDING,
  },
  {
    id: 'ccb-hl-app-03',
    name: 'Portfolio Analytics',
    description: 'Portfolio risk & performance analytics',
    snowPermission: 'Admin',
    team: { name: 'Team Ridgeline', engineers: 6 },
    tower: HOME_LENDING,
  },
]

export const MY_APPS_BY_PERSONA: Record<string, readonly MyApp[]> = {
  jdoe4821: HOME_LENDING_APPS,
  asmith7734: HOME_LENDING_APPS,
}
