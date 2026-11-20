import {test} from 'node:test';
import assert from 'node:assert/strict';
import {postgresOptions} from '../lib/postgres-config.js';
test('database URLs cannot disable TLS certificate verification',()=>{
 const options=postgresOptions('postgresql://user:password@example.com/db?sslmode=no-verify&ssl=false&uselibpqcompat=true&application_name=test');
 const url=new URL(options.connectionString);
 assert.equal(options.ssl.rejectUnauthorized,true);
 assert.equal(url.searchParams.has('sslmode'),false);
 assert.equal(url.searchParams.has('ssl'),false);
 assert.equal(url.searchParams.has('uselibpqcompat'),false);
 assert.equal(url.searchParams.get('application_name'),'test');
 assert.equal(options.statement_timeout,15000);
});
