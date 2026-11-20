// Enforce CA/hostname verification even when a connection URL requests weak SSL.
export function postgresOptions(connectionString) {
  if (connectionString) {
    const url = new URL(connectionString);
    for (const key of ['sslmode','ssl','sslcert','sslkey','sslrootcert','uselibpqcompat']) url.searchParams.delete(key);
    connectionString = url.toString();
  }
  return {connectionString, ssl:{rejectUnauthorized:true}, connectionTimeoutMillis:10000, statement_timeout:15000};
}
