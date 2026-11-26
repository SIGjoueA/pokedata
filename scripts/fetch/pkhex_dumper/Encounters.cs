using System.Reflection;
using System.Text.Json;
using PKHeX.Core;

// Phase 3: encounter templates (wild slots, static / gift / trade / egg / event) and met-location names in 10 languages,
// read from PKHeX.Core's embedded game data. One file per generation; every public scalar member is kept as is.
public static class Encounters {
  static readonly string[] Langs = { "ja", "en", "fr", "de", "it", "es", "es-419", "ko", "zh-Hans", "zh-Hant" };
  static readonly HashSet<string> Skip = new() { "Parent", "Slots", "EqualityContract", "Name", "LongName", "IsShiny" };

  static object Scalar(object v) {
    if (v == null) return null;
    var t = v.GetType();
    if (t.IsEnum) return v.ToString();
    if (t.IsPrimitive || v is string) return v;
    if (v is byte[] ba && ba.Length <= 32) return ba.Select(x => (int)x).ToArray();
    if (v is ushort[] ua && ua.Length <= 32) return ua.Select(x => (int)x).ToArray();
    if (v is Moveset ms) return new[] { (int)ms.Move1, ms.Move2, ms.Move3, ms.Move4 };
    return null;
  }
  static Dictionary<string, object> Dump(object o) {
    var d = new SortedDictionary<string, object>(StringComparer.Ordinal);
    var t = o.GetType(); d["_type"] = t.Name;
    foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance)) {
      if (p.GetIndexParameters().Length > 0 || p.PropertyType.IsByRefLike || Skip.Contains(p.Name)) continue;
      try { var s = Scalar(p.GetValue(o)); if (s != null) d[p.Name] = s; } catch { }
    }
    foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.Instance)) {
      if (Skip.Contains(f.Name)) continue;
      try { var s = Scalar(f.GetValue(o)); if (s != null) d[f.Name] = s; } catch { }
    }
    return new Dictionary<string, object>(d);
  }

  public static void Run(string outDir) {
    var asm = typeof(PersonalTable).Assembly;
    var byGen = new SortedDictionary<string, List<object>>();
    foreach (var t in asm.GetTypes().Where(t => t.Name.StartsWith("Encounters") && t.IsAbstract && t.IsSealed).OrderBy(t => t.Name, StringComparer.Ordinal)) {
      var members = t.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static).OrderBy(f => f.MetadataToken)
          .Select(f => (f.Name, (Func<object>)(() => f.GetValue(null))))
        .Concat(t.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static).OrderBy(p => p.MetadataToken)
          .Where(p => !p.PropertyType.IsByRefLike && p.GetIndexParameters().Length == 0).Select(p => (p.Name, (Func<object>)(() => p.GetValue(null)))));
      foreach (var (name, get) in members) {
        object v; try { v = get(); } catch { continue; }
        IEnumerable<object> items = v is Array a && !a.GetType().GetElementType().IsPrimitive ? a.Cast<object>() : v is IEncounterable ? new[] { v } : Array.Empty<object>();
        foreach (var it in items) {
          if (it == null || it is string) continue;
          var slotsP = it.GetType().GetProperty("Slots");
          if (slotsP != null && slotsP.GetValue(it) is Array slots) {
            var area = Dump(it);
            int ai = 0;
            foreach (var s in slots) {
              var d = Dump(s); d["_area"] = area; d["_table"] = t.Name + "." + name; d["_slot_index"] = ai++;
              Add(byGen, d);
            }
          } else if (it is IEncounterable) { var d = Dump(it); d["_table"] = t.Name + "." + name; Add(byGen, d); }
        }
      }
    }
    foreach (var (g, rows) in byGen) {
      File.WriteAllText(Path.Combine(outDir, $"encounters_{g}.json"), JsonSerializer.Serialize(rows));
      Console.WriteLine($"encounters {g}: {rows.Count}");
    }
    // met-location names, per generation (list of the game named), per bank, per language
    var sets = new (string id, byte gen, GameVersion ver, int[] banks)[] {
      ("gsc", 2, GameVersion.C, new[] { 0 }), ("rsefrlg", 3, GameVersion.E, new[] { 0 }), ("cxd", 3, GameVersion.CXD, new[] { 0 }),
      ("hgss", 4, GameVersion.HG, new[] { 0, 2000, 3000 }), ("bw2", 5, GameVersion.B2, new[] { 0, 30000, 40000, 60000 }),
      ("xy", 6, GameVersion.X, new[] { 0, 30000, 40000, 60000 }), ("sm", 7, GameVersion.SN, new[] { 0, 30000, 40000, 60000 }),
      ("gg", 7, GameVersion.GP, new[] { 0, 30000, 40000, 60000 }), ("swsh", 8, GameVersion.SW, new[] { 0, 30000, 40000, 60000 }),
      ("bdsp", 8, GameVersion.BD, new[] { 0, 30000, 40000, 60000 }), ("la", 8, GameVersion.PLA, new[] { 0, 30000, 40000, 60000 }),
      ("sv", 9, GameVersion.SL, new[] { 0, 30000, 40000, 60000 }), ("za", 9, GameVersion.ZA, new[] { 0, 30000, 40000, 60000 }) };
    var locs = new Dictionary<string, object>();
    foreach (var (id, gen, ver, banks) in sets) {
      var per = new Dictionary<string, Dictionary<string, string>>();
      foreach (var l in Langs) {
        var gs = GameInfo.GetStrings(l);
        var m = new Dictionary<string, string>();
        foreach (var b in banks) {
          string[] names; try { names = gs.GetLocationNames(gen, ver, b).ToArray(); } catch { continue; }
          for (int i = 0; i < names.Length; i++) if (!string.IsNullOrEmpty(names[i])) m[(b + i).ToString()] = names[i];
        }
        per[l] = m;
      }
      locs[id] = per;
    }
    File.WriteAllText(Path.Combine(outDir, "locations.json"), JsonSerializer.Serialize(locs));
    Console.WriteLine("locations ok");
  }
  static void Add(SortedDictionary<string, List<object>> byGen, Dictionary<string, object> d) {
    var g = d.TryGetValue("Generation", out var x) ? x.ToString() : "0";
    if (d.TryGetValue("Context", out var c) && c is string cs && (cs.EndsWith("a") || cs.EndsWith("b"))) g += cs[^1];
    if (!byGen.TryGetValue(g, out var l)) byGen[g] = l = new List<object>();
    l.Add(d);
  }
}
