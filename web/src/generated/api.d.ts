// GENERATED from src/generated/openapi.json by scripts/genApiTypes.ts (O70).
// Do not edit: regenerate with `poetry run python scripts/dump_openapi.py`
// (repo root) then `npm run api:types`. src/generated/api.test.ts guards drift.
export type paths = {
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
        /** Body_post_intake_evidence_intake__intake_id__evidence_post */
        Body_post_intake_evidence_intake__intake_id__evidence_post: {
            /** Files */
            files: string[];
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
            /** Owner Token */
            owner_token: string;
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
         */
        LoginOut: {
            /** Expires At */
            expires_at: string;
            /** Persona Id */
            persona_id: string;
            /** Role */
            role: string;
            /** Token */
            token: string;
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
            /** Keys */
            keys: string[];
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
            /** Watermarked */
            watermarked: boolean;
        };
        /** StatusOut */
        StatusOut: {
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
}
