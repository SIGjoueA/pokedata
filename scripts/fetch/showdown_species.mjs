// Flatten Pokemon Showdown species data for the mods matching each game.
// Usage: node showdown_species.mjs <showdown/data> <out.json>
import fs from 'node:fs';
import path from 'node:path';
const [dataDir, outFile] = process.argv.slice(2);

function loadTable(file, exportName) {
  if (!fs.existsSync(file)) return null;
  let src = fs.readFileSync(file, 'utf8');
  src = src.replace(/export const (\w+)\s*:\s*[^=]+=/g, 'exports.$1 =');
  const exports = {};
  new Function('exports', src)(exports);
  return exports[exportName] || null;
}
function inheritOf(mod) {
  const f = path.join(dataDir, 'mods', mod, 'scripts.ts');
  if (!fs.existsSync(f)) return null;
  const m = fs.readFileSync(f, 'utf8').match(/inherit:\s*'([\w]+)'/);
  return m ? m[1] : null;
}
const base = loadTable(path.join(dataDir, 'pokedex.ts'), 'Pokedex');
const cache = { gen9: base };
function resolve(mod) {
  if (cache[mod]) return cache[mod];
  const parent = resolve(inheritOf(mod) || 'gen9');
  const own = loadTable(path.join(dataDir, 'mods', mod, 'pokedex.ts'), 'Pokedex') || {};
  const merged = { ...parent };
  for (const [id, e] of Object.entries(own)) merged[id] = e.inherit ? { ...(parent[id] || {}), ...e } : e;
  return (cache[mod] = merged);
}
const MODS = { rb: 'gen1', y: 'gen1', gs: 'gen2', c: 'gen2', rs: 'gen3rs', e: 'gen3', frlg: 'gen3frlg',
  dp: 'gen4', pt: 'gen4pt', hgss: 'gen4', bw: 'gen5bw1', b2w2: 'gen5', xy: 'gen6xy', oras: 'gen6',
  sm: 'gen7sm', usum: 'gen7', lgpe: 'gen7letsgo', sw: 'gen8', bdsp: 'gen8bdsp', la: 'gen8legends',
  sv: 'gen9', za: 'gen9legends' };
const out = { mods: MODS, games: {} };
for (const [game, mod] of Object.entries(MODS)) {
  const t = resolve(mod);
  const g = {};
  for (const [id, e] of Object.entries(t)) {
    if (!e || !e.num || e.num <= 0) continue;
    g[id] = { num: e.num, name: e.name, baseSpecies: e.baseSpecies || null, forme: e.forme || null,
      types: e.types, baseStats: e.baseStats, abilities: e.abilities, tags: e.tags || [],
      formeOrder: e.formeOrder || null, heightm: e.heightm, weightkg: e.weightkg };
  }
  out.games[game] = g;
}
fs.writeFileSync(outFile, JSON.stringify(out));
console.log('showdown species', Object.keys(out.games).length);
