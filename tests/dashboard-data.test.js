import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import { snapshot } from '../lib/dashboard.js';
const originals = { connect:pg.Client.prototype.connect, query:pg.Client.prototype.query, end:pg.Client.prototype.end, token:process.env.BOT_TOKEN };
after(()=>{Object.assign(pg.Client.prototype,{connect:originals.connect,query:originals.query,end:originals.end});if(originals.token===undefined)delete process.env.BOT_TOKEN;else process.env.BOT_TOKEN=originals.token;});
test('dashboard snapshot reads only current bot aggregates with empty-state support',async()=>{
 process.env.BOT_TOKEN='999:test';const queries=[];let ended=false;
 pg.Client.prototype.connect=async()=>{};
 pg.Client.prototype.end=async()=>{ended=true;};
 pg.Client.prototype.query=async sql=>{queries.push(sql);if(sql.startsWith('WITH audience'))return {rows:[{summary:{total:0,active:0,setup:0,stopped:0,due:0,next_due:null,groups:[]}}]};if(sql.includes('to_regclass'))return {rows:[{name:null}]};return {rows:[]};};
 const data=await snapshot();assert.equal(data.total,0);assert.deepEqual(data.runs,[]);assert.deepEqual(data.groups,[]);assert.ok(ended);assert.ok(queries.includes('SET LOCAL search_path TO "bot_999"'));assert.ok(queries[0].includes('READ ONLY'));assert.ok(!queries.some(q=>/INSERT|UPDATE|DELETE|CREATE/.test(q)));assert.ok(!JSON.stringify(data).includes('chat_id'));
});
test('dashboard closes the database connection on query failure',async()=>{
 let ended=false;pg.Client.prototype.connect=async()=>{};pg.Client.prototype.end=async()=>{ended=true;};pg.Client.prototype.query=async()=>{throw new Error('test failure');};
 await assert.rejects(snapshot());assert.ok(ended);
});
