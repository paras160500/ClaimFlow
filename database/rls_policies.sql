-- ClaimFlow Row Level Security (RLS) policies.
--
-- IMPORTANT CONTEXT: this Node.js backend uses the SUPABASE_SERVICE_ROLE_KEY
-- for all of its own queries (see src/database/supabase.ts), which BYPASSES
-- RLS entirely by design. Authorization for API requests is enforced by
-- this backend's own middleware (requireAuth + requireRole), not by RLS.
--
-- So why bother with RLS at all? Defense in depth: RLS is what protects the
-- data if someone ever queries Supabase *directly* with the anon/public key
-- (e.g. a future mobile app, a debugging session, a leaked anon key). It
-- should never be the only thing standing between a claim and the internet,
-- but it's a cheap and standard safety net to have in place regardless.

alter table employees enable row level security;
alter table customers enable row level security;
alter table vehicles enable row level security;
alter table policies enable row level security;
alter table policy_versions enable row level security;
alter table claims enable row level security;
alter table repair_shops enable row level security;
alter table investigations enable row level security;
alter table claim_documents enable row level security;
alter table ml_assessments enable row level security;
alter table risk_signals enable row level security;
alter table audit_logs enable row level security;

-- Helper: is the currently-authenticated user (auth.uid()) a known employee?
-- Used below so "any logged-in employee can read" doesn't accidentally mean
-- "any Supabase Auth user anywhere can read".
create or replace function is_claimflow_employee()
returns boolean
language sql
security definer
set search_path = public
as $$
  select exists (
    select 1 from employees where auth_user_id = auth.uid()
  );
$$;

-- Employees can see their own profile; nobody can read other employees'
-- profiles directly via the anon/authenticated key (the Node backend's
-- /api/employees route uses the service-role key, so it's unaffected).
create policy "employees_select_own" on employees
  for select using (auth_user_id = auth.uid());

-- Any logged-in ClaimFlow employee can READ claims/customers/vehicles/etc --
-- this is an internal investigation tool, not a multi-tenant consumer app,
-- so read access is uniform across roles. Writes are intentionally NOT
-- covered by a policy here (default-deny), because all writes are expected
-- to go through the Node backend's service-role client, never directly.
create policy "employees_read_customers" on customers for select using (is_claimflow_employee());
create policy "employees_read_vehicles" on vehicles for select using (is_claimflow_employee());
create policy "employees_read_policies" on policies for select using (is_claimflow_employee());
create policy "employees_read_policy_versions" on policy_versions for select using (is_claimflow_employee());
create policy "employees_read_claims" on claims for select using (is_claimflow_employee());
create policy "employees_read_repair_shops" on repair_shops for select using (is_claimflow_employee());
create policy "employees_read_investigations" on investigations for select using (is_claimflow_employee());
create policy "employees_read_claim_documents" on claim_documents for select using (is_claimflow_employee());
create policy "employees_read_ml_assessments" on ml_assessments for select using (is_claimflow_employee());
create policy "employees_read_risk_signals" on risk_signals for select using (is_claimflow_employee());

-- Audit logs are more sensitive than everything else: only let an employee
-- read entries where they were the actor. The Node backend's Admin-only
-- /api/audit-logs route uses the service-role key and sees everything,
-- regardless of this policy.
create policy "employees_read_own_audit_logs" on audit_logs
  for select using (
    employee_id = (select id::text from employees where auth_user_id = auth.uid())
  );
