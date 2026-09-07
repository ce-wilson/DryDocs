// GENERATED from src/generated/openapi.json by scripts/genApiTypes.ts (O70).
// Do not edit: regenerate with `poetry run python scripts/dump_openapi.py`
// (repo root) then `npm run api:types`. src/generated/api.test.ts guards drift.
export type paths = {
    "/admin/log-estate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Log Estate */
        get: operations["get_log_estate_admin_log_estate_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/config": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Config */
        get: operations["config_config_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/data-centers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Data Centers */
        get: operations["get_data_centers_data_centers_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/demo": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Demo */
        get: operations["get_demo_demo_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/docs-verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Docs Verify */
        get: operations["get_docs_verify_docs_verify_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/exports/{export_id}/manifest": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Export Manifest */
        get: operations["get_export_manifest_exports__export_id__manifest_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/intake": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Intakes */
        get: operations["get_intakes_intake_get"];
        put?: never;
        /** Post Intake */
        post: operations["post_intake_intake_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/intake/{intake_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get One Intake */
        get: operations["get_one_intake_intake__intake_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/intake/{intake_id}/evidence": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Intake Evidence */
        post: operations["post_intake_evidence_intake__intake_id__evidence_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/intake/{intake_id}/thread-decision": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Thread Decision */
        post: operations["post_thread_decision_intake__intake_id__thread_decision_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/intake/{intake_id}/transition": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Intake Transition */
        post: operations["post_intake_transition_intake__intake_id__transition_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Login */
        post: operations["post_login_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Logout */
        post: operations["post_logout_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/app-code/draft": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post App Code Draft */
        post: operations["post_app_code_draft_mappings_app_code_draft_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/app-code/migrations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get App Code Migrations */
        get: operations["get_app_code_migrations_mappings_app_code_migrations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/changeset": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Changeset */
        post: operations["post_changeset_mappings_changeset_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/domains": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Domains */
        get: operations["get_domains_mappings_domains_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/drafts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Drafts */
        get: operations["get_drafts_mappings_drafts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/drafts/{draft_id}/promote": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Promote Draft */
        post: operations["post_promote_draft_mappings_drafts__draft_id__promote_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/grid/{domain_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Grid */
        get: operations["get_grid_mappings_grid__domain_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/options": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Options */
        get: operations["get_options_mappings_options_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/overrides/draft": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Override Draft */
        post: operations["post_override_draft_mappings_overrides_draft_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/overrides/report": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Override Report */
        get: operations["get_override_report_mappings_overrides_report_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/mappings/pending/report": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Pending Report */
        get: operations["get_pending_report_mappings_pending_report_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/queries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Queries */
        get: operations["queries_queries_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/query/{query_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Query */
        post: operations["post_query_query__query_id__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/raw-cypher": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Raw */
        post: operations["post_raw_raw_cypher_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/specs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Specs */
        get: operations["get_specs_specs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/specs/{spec_id}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Spec Export */
        post: operations["post_spec_export_specs__spec_id__export_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/specs/{spec_id}/run": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Spec Run */
        post: operations["post_spec_run_specs__spec_id__run_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/specs/ephemeral": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Ephemeral Register */
        post: operations["post_ephemeral_register_specs_ephemeral_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
};
export type webhooks = Record<string, never>;
export type components = {
    schemas: {
        /**
         * AppCodeMigrationsOut
         * @description GET /mappings/app-code/migrations — the K7 §B2 tier-3 readback, so a
         *     declared end state has a reader and "temporarily dual-coded" cannot quietly
         *     become the permanent state nobody re-opens. A row is ``SELECT *`` over
         *     ``v_dual_coded_migrations``, so the row shape is the view's.
         */
        AppCodeMigrationsOut: {
            /** Count */
            count: number;
            /** Migrations */
            migrations: {
                [key: string]: unknown;
            }[];
        };
        /** Body_post_intake_evidence_intake__intake_id__evidence_post */
        Body_post_intake_evidence_intake__intake_id__evidence_post: {
            /** Files */
            files: Blob[];
        };
        /**
         * CauseOut
         * @description R15: one cause that limited a walk. `cause` is the DryDocs cause class
         *     (`unparsed-cmd-line` | `unresolved-invocation` | `gate-pending-edge`),
         *     `detail` names the concrete thing (the probe class, or the planned
         *     vocabulary entry id for a gate-pending edge), `count` is the measurement
         *     when one was taken and null when it could not be (a probe that returned no
         *     count) or does not apply (a gate-pending edge has no count until it exists).
         */
        CauseOut: {
            /** Cause */
            cause: string;
            /** Count */
            count?: number | null;
            /** Detail */
            detail: string;
        };
        /**
         * ChangesetArtifactOut
         * @description POST /mappings/changeset. An ARTIFACT, not a write: the server produces
         *     CSV text and a manifest snippet and writes nothing at all — the loader stays
         *     the only graph writer (wf-mapping-01's one rule). ``lifecycle`` and ``note``
         *     carry that instruction to the operator, which is why they are on the wire
         *     and not in the page.
         */
        ChangesetArtifactOut: {
            /** Csv */
            csv: string;
            /** Entries */
            entries: number;
            /** Filename */
            filename: string;
            /** Lifecycle */
            lifecycle: string;
            /** Manifest Snippet */
            manifest_snippet: string;
            /** Note */
            note: string;
        };
        /** ChangesetBody */
        ChangesetBody: {
            /** Draft Id */
            draft_id?: string | null;
            /**
             * Entries
             * @default []
             */
            entries: unknown[];
        };
        /** ColumnOut */
        ColumnOut: {
            /** Label */
            label: string;
            /** Name */
            name: string;
            /** Type */
            type: string;
        };
        /**
         * ConfigOut
         * @description GET /config (ADR 0020): the non-secret, per-environment values the console
         *     reads at boot instead of having them inlined at build time. Nothing here may
         *     be a credential or a coordinate the page could not already reach.
         */
        ConfigOut: {
            /** Runtime View Url Template */
            runtime_view_url_template: string | null;
        };
        /**
         * CorpusRowOut
         * @description One declared corpus, reconciled against the graph.
         */
        CorpusRowOut: {
            /** Chunks */
            chunks: number;
            /** Corpus Id */
            corpus_id: string;
            /** Detail */
            detail: string;
            /** Documents */
            documents: number;
            /** Ok */
            ok: boolean;
            /** Status */
            status: string;
            /** Target Db */
            target_db: string;
        };
        /**
         * CorpusStatusOut
         * @description GET /docs-verify. ``databases_queried`` is carried beside
         *     ``databases_swept`` because the surface's honesty rule turns on the
         *     difference: a database that was not queried renders "not queried", never 0
         *     (the O56 rule), and the rows alone cannot tell those apart. ``statuses`` is
         *     the whole vocabulary, sent with the payload so the page renders the real set
         *     instead of a hand-copied one.
         */
        CorpusStatusOut: {
            /** Classification */
            classification: string;
            /** Databases Queried */
            databases_queried: string[];
            /** Databases Swept */
            databases_swept: string[];
            /** Rows */
            rows: components["schemas"]["CorpusRowOut"][];
            /** Statuses */
            statuses: string[];
        };
        /**
         * CorrectionsReportOut
         * @description GET /mappings/overrides/report — the AO-facing source-corrections
         *     artifact, rendered as markdown the steward can send on.
         */
        CorrectionsReportOut: {
            /** Count */
            count: number;
            /** Filename */
            filename: string;
            /** Generated By */
            generated_by: string;
            /** Generated On */
            generated_on: string;
            /** Markdown */
            markdown: string;
        };
        /**
         * DataCenterOut
         * @description One row of the data-center spelling registry (LOAD2), as the console reads
         *     it for Z6's runtime map.
         *
         *     ``default_time`` and ``suffix`` are OPTIONAL BY RULE and not by accident: the
         *     ``E####``-as-default-time reading comes from an internal standard whose own
         *     open items include "confirm E is always Eastern", so a name that carries no
         *     time segment registers exactly like one that does. They are declared here as
         *     plain strings that may be empty for that reason — a null would suggest the
         *     lookup failed, and nothing failed.
         */
        DataCenterOut: {
            /** Code */
            code: string;
            /** Default Time */
            default_time: string;
            /** Name */
            name: string;
            /** Note */
            note: string;
            /** Sample */
            sample: boolean;
            /** Suffix */
            suffix: string;
        };
        /**
         * DataCentersOut
         * @description GET /data-centers.
         *
         *     ``source`` names the venue the rows came from (J18): the machine-local
         *     internal twin, or the publishable synthetic sample. A console that showed a
         *     default time without saying which file it read would make a producer-side
         *     demo look like a statement about production.
         */
        DataCentersOut: {
            /** Data Centers */
            data_centers: components["schemas"]["DataCenterOut"][];
            /** Source */
            source: string;
            /** Updated */
            updated: string;
        };
        /**
         * DraftReceiptOut
         * @description POST /mappings/overrides/draft and /mappings/app-code/draft (S4, ADR 0009
         *     rule 5). Drafting writes ROWS to the mapping.db buffer and hands back this
         *     receipt. The shape it replaced returned a whole replacement file, which
         *     could not survive two editors: each held a full file built from the same
         *     base, so whichever was committed last erased the other.
         */
        DraftReceiptOut: {
            /** Committed Rows */
            committed_rows: number;
            /** Domain */
            domain: string;
            /** Draft Id */
            draft_id: string;
            /** Entries */
            entries: number;
            /** Note */
            note: string;
            /** Pending */
            pending: number;
        };
        /** EphemeralRegisterBody */
        EphemeralRegisterBody: {
            /**
             * Columns
             * @default []
             */
            columns: unknown[];
            /** Cypher */
            cypher: string;
            /** Database */
            database: string;
            /**
             * Description
             * @default
             */
            description: string;
            /** Owner Session */
            owner_session: string;
            /**
             * Params
             * @default {}
             */
            params: {
                [key: string]: unknown;
            };
        };
        /**
         * EphemeralRegisterOut
         * @description POST /specs/ephemeral. The console never calls this one — the QA agent
         *     registers Cypher here and receives a REF, then runs and exports through the
         *     same reviewed seam every other caller uses, so the Cypher itself is never a
         *     query parameter. Modelled with the rest because O70 named it in the same
         *     list, and because the agent tier is a client with the same claim on a
         *     declared response as the browser has.
         */
        EphemeralRegisterOut: {
            /** Classification */
            classification: string;
            /** Database */
            database: string;
            /** Expires At */
            expires_at: string;
            /** Explore Ref */
            explore_ref: string;
            /** Watermarked */
            watermarked: boolean;
        };
        /**
         * EvidenceOut
         * @description One uploaded evidence file. ``kind`` is the extension with its dot
         *     stripped, and the upload path admits exactly three (``ALLOWED_EXTENSIONS``),
         *     so the wire declares the three rather than a bare string.
         */
        EvidenceOut: {
            /** Evidence Id */
            evidence_id: string;
            /** Filename */
            filename: string;
            /** Intake Id */
            intake_id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "msg" | "json" | "txt";
            /** Pair Key */
            pair_key: string;
            /** Preview */
            preview: {
                [key: string]: unknown;
            } | null;
            /** Rel Key */
            rel_key: string;
            /** Sha256 */
            sha256: string;
            /** Size */
            size: number;
            /** Superseded */
            superseded: boolean;
            /** Uploaded At */
            uploaded_at: string;
        };
        /**
         * ExportBody
         * @description The export request: a spec run's params, plus API1 (c)'s raisable ceiling.
         *
         *     A separate model from ``QueryBody`` because the ceiling is an EXPORT
         *     decision. Raising the limit on a grid read would change what is on screen;
         *     raising it here changes what lands in a file that carries a manifest, and
         *     those are different permissions to grant. Omitted (the default) keeps
         *     today's behaviour exactly — the display limit the console echoes back — so
         *     a caller that has not been updated is unaffected.
         */
        ExportBody: {
            /** Limit */
            limit?: number | null;
            /**
             * Params
             * @default {}
             */
            params: {
                [key: string]: unknown;
            };
        };
        /** HealthOut */
        HealthOut: {
            /** Status */
            status: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** IntakeCreateBody */
        IntakeCreateBody: {
            /**
             * Area
             * @default {}
             */
            area: {
                [key: string]: unknown;
            };
            /** Context Type */
            context_type: string;
            /**
             * Note
             * @default
             */
            note: string;
        };
        /**
         * IntakeEvidenceOut
         * @description POST /intake/{intake_id}/evidence: the whole record, plus the id of the
         *     file just stored. ``_evidence_out`` adds that one key to what ``get_intake``
         *     returns, which makes it a THIRD shape on this surface — and under
         *     ``extra='forbid'`` a model that overlooked it would turn every SUCCESSFUL
         *     upload into a response-validation 500.
         */
        IntakeEvidenceOut: {
            /** Area */
            area: {
                [key: string]: string | null;
            };
            /** Classification */
            classification: string;
            /** Context Type */
            context_type: string;
            /** Created At */
            created_at: string;
            /** Created By */
            created_by: string;
            /** Evidence */
            evidence: components["schemas"]["EvidenceOut"][];
            /** Evidence Id */
            evidence_id: string;
            /** Intake Id */
            intake_id: string;
            legal_transitions: components["schemas"]["LegalTransitionsOut"];
            /** Note */
            note: string;
            /** Origin */
            origin: string;
            /** Review Payload */
            review_payload: string | null;
            /** Status */
            status: string;
            /** Thread Decision */
            thread_decision: ("adds-value" | "no-new-value") | null;
            /** Thread Flagged */
            thread_flagged: boolean;
            /** Thread Of */
            thread_of: string[];
        };
        /** IntakeListOut */
        IntakeListOut: {
            /** Intakes */
            intakes: components["schemas"]["IntakeListRowOut"][];
        };
        /**
         * IntakeListRowOut
         * @description An intake as the QUEUE lists it.
         *
         *     NO ``evidence`` FIELD — and that is the list's real shape, not an omission
         *     here. ``list_intakes`` serializes each record and attaches its legal
         *     transitions; it never reads the evidence table, which is one query for the
         *     page instead of one per row. The console declared the list as
         *     ``IntakeRecord[]`` — the same type it uses for a single record — so it has
         *     been claiming an always-present ``evidence: EvidenceRow[]`` that the list
         *     endpoint has never sent. Modelling the two shapes apart is what surfaced
         *     that, and keeping them apart is what stops it coming back.
         */
        IntakeListRowOut: {
            /** Area */
            area: {
                [key: string]: string | null;
            };
            /** Classification */
            classification: string;
            /** Context Type */
            context_type: string;
            /** Created At */
            created_at: string;
            /** Created By */
            created_by: string;
            /** Intake Id */
            intake_id: string;
            legal_transitions: components["schemas"]["LegalTransitionsOut"];
            /** Note */
            note: string;
            /** Origin */
            origin: string;
            /** Review Payload */
            review_payload: string | null;
            /** Status */
            status: string;
            /** Thread Decision */
            thread_decision: ("adds-value" | "no-new-value") | null;
            /** Thread Flagged */
            thread_flagged: boolean;
            /** Thread Of */
            thread_of: string[];
        };
        /**
         * IntakeRecordOut
         * @description One intake read whole: the list row, plus the evidence ``get_intake``
         *     attaches. Every single-record route on this surface returns this shape,
         *     because create, transition and thread-decision all end by re-reading the
         *     record through ``get_intake``.
         */
        IntakeRecordOut: {
            /** Area */
            area: {
                [key: string]: string | null;
            };
            /** Classification */
            classification: string;
            /** Context Type */
            context_type: string;
            /** Created At */
            created_at: string;
            /** Created By */
            created_by: string;
            /** Evidence */
            evidence: components["schemas"]["EvidenceOut"][];
            /** Intake Id */
            intake_id: string;
            legal_transitions: components["schemas"]["LegalTransitionsOut"];
            /** Note */
            note: string;
            /** Origin */
            origin: string;
            /** Review Payload */
            review_payload: string | null;
            /** Status */
            status: string;
            /** Thread Decision */
            thread_decision: ("adds-value" | "no-new-value") | null;
            /** Thread Flagged */
            thread_flagged: boolean;
            /** Thread Of */
            thread_of: string[];
        };
        /** IntakeTransitionBody */
        IntakeTransitionBody: {
            /**
             * Note
             * @default
             */
            note: string;
            /** To */
            to: string;
        };
        /** LegalTransitionOut */
        LegalTransitionOut: {
            /** Action */
            action: string;
            /** To */
            to: string;
        };
        /**
         * LegalTransitionsOut
         * @description The per-record, per-ROLE transition map the UI renders its buttons from —
         *     the server owns the machine (the IntakeStepper decision, 2026-08-06), so the
         *     button set is a server answer and never a client rule.
         *
         *     The two thread fields carry defaults where nothing else here does, because
         *     the handler only attaches them to a flagged draft that still owes its
         *     decision. A default keeps them out of the schema's ``required`` list, which
         *     is what makes the generated client declare them optional — matching the
         *     handler instead of over-promising for it.
         */
        LegalTransitionsOut: {
            /** Status */
            status: string;
            /** Terminal */
            terminal: boolean;
            /**
             * Thread Decision Required
             * @default false
             */
            thread_decision_required: boolean;
            /**
             * Thread Decisions
             * @default []
             */
            thread_decisions: string[];
            /** Transitions */
            transitions: components["schemas"]["LegalTransitionOut"][];
            /** Waiting On Gate */
            waiting_on_gate: boolean;
        };
        /**
         * LogEstateOut
         * @description GET /admin/log-estate. Both halves ride in one payload because the SME's
         *     question spans them. Note what is absent and stays absent: a kind's
         *     CONTENTS. ADR 0014 clause 6 rules that the verbose debug tier is captured;
         *     SURFACING it is a different risk and is not ruled, so there is no field here
         *     through which a log line could travel.
         */
        LogEstateOut: {
            /** Kinds */
            kinds: components["schemas"]["LogKindOut"][];
            /** Zones */
            zones: components["schemas"]["LogZoneOut"][];
        };
        /** LoginBody */
        LoginBody: {
            /** Persona Id */
            persona_id: string;
            /** Secret */
            secret: string;
        };
        /**
         * LoginOut
         * @description The session the browser holds. Never the secret (O69).
         *
         *     ``session_id`` (ADR 0019) is the public handle: the console passes it to the
         *     graph_qa agent in the control part so the agent can register ephemeral specs
         *     for THIS session without ever holding the token. It authorizes nothing.
         */
        LoginOut: {
            /** Expires At */
            expires_at: string;
            /** Persona Id */
            persona_id: string;
            /** Role */
            role: string;
            /** Session Id */
            session_id: string;
            /** Token */
            token: string;
        };
        /**
         * LogKindOut
         * @description One declared log kind, beside what is actually on the host's disk.
         *
         *     ``dir`` and ``oldest_days`` are nullable but always PRESENT: a kind with no
         *     files has no oldest file, and that is a different fact from a kind whose age
         *     was never measured.
         */
        LogKindOut: {
            /** Dir */
            dir: string | null;
            /** Exists */
            exists: boolean;
            /** File Count */
            file_count: number;
            /** Format */
            format: string;
            /** Id */
            id: string;
            /** Level */
            level: string;
            /** Oldest Days */
            oldest_days: number | null;
            /** Over Retention */
            over_retention: boolean;
            /** Path */
            path: string;
            /** Retention Days */
            retention_days: number;
            /** Rotation */
            rotation: string;
            /** Status */
            status: string;
            /** Total Bytes */
            total_bytes: number;
        };
        /**
         * LogZoneOut
         * @description One declared data zone (G109), inventoried the same way.
         */
        LogZoneOut: {
            /** Empty */
            empty: boolean;
            /** Exists */
            exists: boolean;
            /** File Count */
            file_count: number;
            /** Id */
            id: string;
            /** Mode */
            mode: string | null;
            /** Path */
            path: string;
            /** Total Bytes */
            total_bytes: number;
        };
        /**
         * MappingDomainOut
         * @description One mapping domain the console can offer. ``available`` is false for a
         *     domain whose reconciler table is not built yet — declared so the page can
         *     render it greyed rather than omit it.
         */
        MappingDomainOut: {
            /** Available */
            available: boolean;
            /** Id */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "quintuple" | "manual" | "override" | "defined";
            /** Source */
            source: string;
            /** Tier */
            tier: number | null;
            /** Title */
            title: string;
        };
        /** MappingDomainsOut */
        MappingDomainsOut: {
            /** Domains */
            domains: components["schemas"]["MappingDomainOut"][];
        };
        /**
         * MappingGridOut
         * @description GET /mappings/grid/{domain_id}. ``keys`` names the columns for THIS
         *     domain and ``rows`` carries them — see the note above on why the row shape
         *     stays open.
         */
        MappingGridOut: {
            /** Domain */
            domain: string;
            /** Keys */
            keys: string[];
            /** Rows */
            rows: {
                [key: string]: unknown;
            }[];
        };
        /**
         * MappingOptionsOut
         * @description GET /mappings/options — the vocabulary the authoring cascade offers.
         */
        MappingOptionsOut: {
            /** Labels */
            labels: {
                [key: string]: unknown;
            }[];
            /** Relationships */
            relationships: {
                [key: string]: unknown;
            }[];
            /** Status Summary */
            status_summary: components["schemas"]["StatusSummaryOut"][];
        };
        /** NamedQueryOut */
        NamedQueryOut: {
            /** Description */
            description: string;
            /** Id */
            id: string;
            /** Params */
            params: components["schemas"]["ParamOut"][];
        };
        /**
         * NamedRunOut
         * @description ``/query/{query_id}`` and ``/raw-cypher`` share this envelope — the
         *     database is named AFTER the fact because routing is a server decision
         *     (ADR 0002 / ADR 0005 decision 2).
         */
        NamedRunOut: {
            /** Database */
            database: string;
            /** Diagnostics */
            diagnostics: {
                [key: string]: unknown;
            };
            /** Keys */
            keys: string[];
            /** Query Id */
            query_id: string;
            /** Rows */
            rows: {
                [key: string]: unknown;
            }[];
        };
        /** OpenDraftOut */
        OpenDraftOut: {
            /** Authored By */
            authored_by: string;
            /** Authored On */
            authored_on: string;
            /** Domain */
            domain: string;
            /** Draft Id */
            draft_id: string;
            /** Entries */
            entries: number;
        };
        /** OpenDraftsOut */
        OpenDraftsOut: {
            /** Drafts */
            drafts: components["schemas"]["OpenDraftOut"][];
        };
        /**
         * ParamOut
         * @description One declared parameter of a named query or a QuerySpec.
         */
        ParamOut: {
            /** Default */
            default?: unknown;
            /** Name */
            name: string;
            /** Required */
            required: boolean;
            /** Type */
            type: string;
        };
        /**
         * PendingCorrectionsReportOut
         * @description GET /mappings/pending/report — the N14 union report, which is the
         *     corrections report plus the per-domain counts behind its total.
         */
        PendingCorrectionsReportOut: {
            /** Count */
            count: number;
            counts: components["schemas"]["PendingCountsOut"];
            /** Filename */
            filename: string;
            /** Generated By */
            generated_by: string;
            /** Generated On */
            generated_on: string;
            /** Markdown */
            markdown: string;
        };
        /**
         * PendingCountsOut
         * @description N14 §D2. ``email_unassigned`` is null when the graph could not be reached
         *     — a rendered state ("read it at the spec"), never an error and never a
         *     silent zero.
         */
        PendingCountsOut: {
            /** Email Unassigned */
            email_unassigned: number | null;
            /** Manual Sources */
            manual_sources: number;
            /** Overrides */
            overrides: number;
        };
        /**
         * PromotedDiffOut
         * @description POST /mappings/drafts/{draft_id}/promote — the unified diff to apply on a
         *     branch. The server still writes nothing; git is the only commit target.
         */
        PromotedDiffOut: {
            /** Diff */
            diff: string;
            /** Domain */
            domain: string;
            /** Draft Id */
            draft_id: string;
            /** Entries */
            entries: number;
            /** Filename */
            filename: string;
            /** Note */
            note: string;
            /** Path */
            path: string;
        };
        /** QueryBody */
        QueryBody: {
            /**
             * Params
             * @default {}
             */
            params: {
                [key: string]: unknown;
            };
        };
        /** RawBody */
        RawBody: {
            /** Cypher */
            cypher: string;
        };
        /**
         * SpecOut
         * @description One registry row as ``/specs`` lists it — the declaration, never the
         *     database (G102: ``watermarked`` comes from the spec).
         */
        SpecOut: {
            /** Classification */
            classification: string;
            /** Columns */
            columns: components["schemas"]["ColumnOut"][];
            /** Cypher */
            cypher: string;
            /** Database */
            database: string;
            /** Description */
            description: string;
            /** Id */
            id: string;
            /** Params */
            params: components["schemas"]["ParamOut"][];
            /** Watermarked */
            watermarked: boolean;
        };
        /**
         * SpecRunOut
         * @description A QuerySpec run (O11): the registry echoes the spec's contract back
         *     with the rows, so the UI renders the classification banner and the
         *     SYNTHESIZED watermark without holding its own query definitions. This is
         *     the server-side twin of the console's ``SpecResult`` seam type.
         */
        SpecRunOut: {
            /**
             * Causes
             * @default []
             */
            causes: components["schemas"]["CauseOut"][];
            /** Classification */
            classification: string;
            /** Columns */
            columns: components["schemas"]["ColumnOut"][];
            /** Cypher */
            cypher: string;
            /** Database */
            database: string;
            /** Ephemeral */
            ephemeral: boolean;
            /** Epistemic */
            epistemic?: ("exact" | "lower-bound") | null;
            /** Keys */
            keys: string[];
            /** Limit */
            limit?: number | null;
            /** Params */
            params: {
                [key: string]: unknown;
            };
            /** Rows */
            rows: {
                [key: string]: unknown;
            }[];
            /** Spec Id */
            spec_id: string;
            /** Truncated */
            truncated: boolean;
            /** Watermarked */
            watermarked: boolean;
        };
        /** StatusOut */
        StatusOut: {
            /** Status */
            status: string;
        };
        /** StatusSummaryOut */
        StatusSummaryOut: {
            /** N */
            n: number;
            /** Status */
            status: string;
        };
        /** ThreadDecisionBody */
        ThreadDecisionBody: {
            /** Decision */
            decision: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
};
export type $defs = Record<string, never>;
export interface operations {
    get_log_estate_admin_log_estate_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LogEstateOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    config_config_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConfigOut"];
                };
            };
        };
    };
    get_data_centers_data_centers_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DataCentersOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_demo_demo_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_docs_verify_docs_verify_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CorpusStatusOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_export_manifest_exports__export_id__manifest_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                export_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthOut"];
                };
            };
        };
    };
    get_intakes_intake_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IntakeListOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_intake_intake_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IntakeCreateBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IntakeRecordOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_one_intake_intake__intake_id__get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                intake_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IntakeRecordOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_intake_evidence_intake__intake_id__evidence_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                intake_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_post_intake_evidence_intake__intake_id__evidence_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IntakeEvidenceOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_thread_decision_intake__intake_id__thread_decision_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                intake_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ThreadDecisionBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IntakeRecordOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_intake_transition_intake__intake_id__transition_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                intake_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IntakeTransitionBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IntakeRecordOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_login_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_logout_logout_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StatusOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_app_code_draft_mappings_app_code_draft_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangesetBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DraftReceiptOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_app_code_migrations_mappings_app_code_migrations_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AppCodeMigrationsOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_changeset_mappings_changeset_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangesetBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangesetArtifactOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_domains_mappings_domains_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MappingDomainsOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_drafts_mappings_drafts_get: {
        parameters: {
            query?: {
                domain?: string | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OpenDraftsOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_promote_draft_mappings_drafts__draft_id__promote_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                draft_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PromotedDiffOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_grid_mappings_grid__domain_id__get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                domain_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MappingGridOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_options_mappings_options_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MappingOptionsOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_override_draft_mappings_overrides_draft_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangesetBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DraftReceiptOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_override_report_mappings_overrides_report_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CorrectionsReportOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_pending_report_mappings_pending_report_get: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PendingCorrectionsReportOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    queries_queries_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NamedQueryOut"][];
                };
            };
        };
    };
    post_query_query__query_id__post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
                "x-drydocs-run-id"?: string | null;
            };
            path: {
                query_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["QueryBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NamedRunOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_raw_raw_cypher_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
                "x-drydocs-run-id"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RawBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NamedRunOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_specs_specs_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SpecOut"][];
                };
            };
        };
    };
    post_spec_export_specs__spec_id__export_post: {
        parameters: {
            query?: {
                format?: string;
            };
            header?: {
                authorization?: string | null;
                "x-drydocs-run-id"?: string | null;
            };
            path: {
                spec_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExportBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_spec_run_specs__spec_id__run_post: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
                "x-drydocs-run-id"?: string | null;
            };
            path: {
                spec_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["QueryBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SpecRunOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_ephemeral_register_specs_ephemeral_post: {
        parameters: {
            query?: never;
            header?: {
                "x-drydocs-agent-key"?: string | null;
                "x-drydocs-run-id"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EphemeralRegisterBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EphemeralRegisterOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
