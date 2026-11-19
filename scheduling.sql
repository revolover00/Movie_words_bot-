-- One shared schedule calculation for the webhook and delivery worker.
-- Strictly advance past the reference instant; never drift with processing time.
CREATE OR REPLACE FUNCTION next_delivery_at(minutes INTEGER, reference_time TIMESTAMPTZ DEFAULT now())
RETURNS TIMESTAMPTZ LANGUAGE SQL IMMUTABLE STRICT AS $$
    SELECT CASE WHEN minutes = 30 THEN
        to_timestamp(((floor(extract(epoch FROM reference_time) / 1800) + 1) * 1800)::double precision)
    ELSE reference_time + make_interval(mins => minutes) END
$$;

-- Align future legacy half-hour schedules once, without postponing overdue work.
UPDATE subscriber_preferences
SET next_due_at = next_delivery_at(30), updated_at = now()
WHERE interval_minutes = 30 AND next_due_at > now()
  AND mod(extract(epoch FROM next_due_at), 1800) <> 0;
