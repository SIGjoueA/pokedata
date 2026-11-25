// Flatten Pokemon Showdown moves, evolution fields and learnsets for the mods matching each game.
// Usage: node showdown_more.mjs <showdown/data> <out.json>
import fs from 'node:fs';
import path from 'node:path';
const [dataDir, outFile] = process.argv.slice(2);

const loaded = {};
async function loadTable(file, exportName) {
  if (!fs.existsSync(file)) return null;
  if (!(file in loaded)) loaded[file] = await import(file);   // Node >= 23 strips TypeScript types natively
  return loaded[file][exportName] || null;
}
function inheritOf(mod) {
  const f = path.join(dataDir, 'mods', mod, 'scripts.ts');
  if (!fs.existsSync(f)) return null;
  const m = fs.readFileSync(f, 'utf8').match(/inherit:\s*'([\w]+)'/);
  return m ? m[1] : null;
}
function resolver(file, exportName) {
  const cache = {};
  const r = async (mod) => {
    if (cache[mod]) return cache[mod];
    if (mod === 'gen9') return (cache.gen9 = (await loadTable(path.join(dataDir, file), exportName)) || {});
    const parent = await r(inheritOf(mod) || 'gen9');
    const own = (await loadTable(path.join(dataDir, 'mods', mod, file), exportName)) || {};
    const merged = { ...parent };
    for (const [id, e] of Object.entries(own)) merged[id] = e.inherit ? { ...(parent[id] || {}), ...e } : e;
    return (cache[mod] = merged);
  };
  return r;
}
const MODS = { rb: 'gen1', y: 'gen1', gs: 'gen2', c: 'gen2', rs: 'gen3rs', e: 'gen3', frlg: 'gen3frlg',
  dp: 'gen4', pt: 'gen4pt', hgss: 'gen4', bw: 'gen5bw1', b2w2: 'gen5', xy: 'gen6xy', oras: 'gen6',
  sm: 'gen7sm', usum: 'gen7', lgpe: 'gen7letsgo', sw: 'gen8', bdsp: 'gen8bdsp', la: 'gen8legends',
  sv: 'gen9', za: 'gen9legends' };
const moves = resolver('moves.ts', 'Moves');
const dex = resolver('pokedex.ts', 'Pokedex');
const out = { mods: MODS, moves: {}, evos: {}, learnsets: {} };
for (const [game, mod] of Object.entries(MODS)) {
  const mv = (await moves(mod)) || {};
  const g = {};
  for (const [id, e] of Object.entries(mv)) {
    if (!e || !e.num || e.num <= 0) continue;
    g[id] = { num: e.num, name: e.name, type: e.type, category: e.category, basePower: e.basePower, accuracy: e.accuracy, pp: e.pp,
      priority: e.priority, target: e.target, flags: Object.keys(e.flags || {}).sort(), secondary: e.secondary ? (e.secondary.chance ?? null) : null,
      isNonstandard: e.isNonstandard || null, isZ: e.isZ || null, isMax: e.isMax || null };
  }
  out.moves[game] = g;
  const d = (await dex(mod)) || {};
  const ev = {};
  for (const [id, e] of Object.entries(d)) {
    if (!e || !e.prevo) continue;
    ev[id] = { num: e.num, name: e.name, prevo: e.prevo, evoType: e.evoType || 'level', evoLevel: e.evoLevel ?? null, evoItem: e.evoItem || null,
      evoMove: e.evoMove || null, evoCondition: e.evoCondition || null, gender: e.gender || null };
  }
  out.evos[game] = ev;
}
// learnsets: base file (all generations, sources like "9L12") + mods that ship their own learnsets
const lsMods = ['gen9', 'gen2', 'gen3rs', 'gen3frlg', 'gen4pt', 'gen5bw1', 'gen6', 'gen6xy', 'gen7sm', 'gen7letsgo', 'gen8', 'gen8bdsp', 'gen8legends', 'gen9legends'];
for (const mod of lsMods) {
  const f = mod === 'gen9' ? path.join(dataDir, 'learnsets.ts') : path.join(dataDir, 'mods', mod, 'learnsets.ts');
  const t = await loadTable(f, 'Learnsets');
  if (!t) continue;
  const o = {};
  for (const [id, e] of Object.entries(t)) if (e && e.learnset) o[id] = e.learnset;
  out.learnsets[mod] = o;
}
fs.writeFileSync(outFile, JSON.stringify(out));
console.log('showdown more', Object.keys(out.moves).length, Object.keys(out.learnsets));
