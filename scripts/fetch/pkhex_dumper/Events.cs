using System.Reflection;
using System.Text.Json;
using PKHeX.Core;

// Phase 3: Mystery Gift database embedded in PKHeX.Core (EncounterEvent.MGDB_*: PCD/PGT, PGF, WC6, WC7, WB7, WC8, WB8, WA8,
// WC9, WA9…), generations 4 and later. Only the facts needed for availability are kept (species, form, origin, egg).
public static class Events {
  static readonly string[] Keep = { "Species", "Form", "Generation", "Context", "Version", "IsEgg", "Location", "EggLocation",
                                    "Level", "Shiny", "CardID", "CardTitle", "FatefulEncounter", "OriginGame", "RestrictVersion" };
  public static void Run(string outDir) {
    var rows = new List<object>();
    foreach (var f in typeof(EncounterEvent).GetFields(BindingFlags.Public | BindingFlags.Static).OrderBy(f => f.Name, StringComparer.Ordinal)) {
      if (f.GetValue(null) is not Array arr) continue;
      foreach (var it in arr) {
        if (it is not MysteryGift g || !g.IsEntity) continue;
        var d = new SortedDictionary<string, object>(StringComparer.Ordinal) { ["_db"] = f.Name, ["_type"] = it.GetType().Name };
        foreach (var k in Keep) {
          var p = it.GetType().GetProperty(k, BindingFlags.Public | BindingFlags.Instance);
          if (p == null || p.GetIndexParameters().Length > 0) continue;
          try {
            var v = p.GetValue(it);
            if (v == null) continue;
            d[k] = v.GetType().IsEnum ? v.ToString() : v;
          } catch { }
        }
        rows.Add(d);
      }
    }
    File.WriteAllText(Path.Combine(outDir, "events.json"), JsonSerializer.Serialize(rows));
    Console.WriteLine($"events: {rows.Count}");
  }
}
