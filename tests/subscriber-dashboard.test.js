import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import pg from 'pg';
import { PGlite } from '@electric-sql/pglite';
import { snapshot } from '../lib/dashboard.js';

test('private subscriber list uses real SQL, bounded pages and parameterized literal search', async()=>{
  const db=new PGlite();
  const old={connect:pg.Client.prototype.connect,query:pg.Client.prototype.query,end:pg.Client.prototype.end,token:process.env.BOT_TOKEN};
  try {
    await db.exec('CREATE SCHEMA bot_999; SET search_path TO bot_999;');
    for(const file of ['schema.sql','scheduling.sql','reliability.sql'])await db.exec(readFileSync(new URL('../'+file,import.meta.url),'utf8'));
    await db.exec("INSERT INTO subscribers(chat_id,username,first_name) SELECT n,'user'||n,'Name' FROM generate_series(1,55) n; INSERT INTO subscriber_preferences(chat_id) VALUES(1);");
    process.env.BOT_TOKEN='999:test';
    pg.Client.prototype.connect=async()=>{};
    pg.Client.prototype.end=async()=>{};
    pg.Client.prototype.query=async(q,p)=>db.query(q,p);
    const first=await snapshot();
    assert.equal(first.subscribers.total,55);
    assert.equal(first.subscribers.rows.length,50);
    assert.equal(typeof first.subscribers.rows[0].chat_id,'string');
    const second=await snapshot({page:2});
    assert.equal(second.subscribers.rows.length,5);
    const found=await snapshot({search:'user55'});
    assert.equal(found.subscribers.rows.length,1);
    assert.equal(found.subscribers.rows[0].username,'user55');
    assert.equal((await snapshot({search:"' OR TRUE --"})).subscribers.total,0);
    assert.equal((await snapshot({search:'%'})).subscribers.total,0);
    assert.equal((await snapshot({page:-1})).subscribers.page,1);
  } finally {
    Object.assign(pg.Client.prototype,{connect:old.connect,query:old.query,end:old.end});
    if(old.token===undefined)delete process.env.BOT_TOKEN;else process.env.BOT_TOKEN=old.token;
    await db.close();
  }
});
