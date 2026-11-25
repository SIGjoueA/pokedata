using System.Text.Json;
using PKHeX.Core;

// Phase 1b / 2: evolutions, move tables, machines, learnsets (all read from PKHeX.Core's embedded game data).
public static class Extra {
  static readonly string[] Langs = { "ja", "en", "fr", "de", "it", "es", "es-419", "ko", "zh-Hans", "zh-Hant" };

  public static void Run(string outDir) {
    var en = GameInfo.GetStrings("en");
    // ---- evolutions per context
    var ctxs = new (string id, EntityContext ctx, IPersonalTable t)[] {
      ("gen1", EntityContext.Gen1, PersonalTable.Y), ("gen2", EntityContext.Gen2, PersonalTable.C), ("gen3", EntityContext.Gen3, PersonalTable.E),
      ("gen4", EntityContext.Gen4, PersonalTable.HGSS), ("gen5", EntityContext.Gen5, PersonalTable.B2W2), ("gen6", EntityContext.Gen6, PersonalTable.AO),
      ("gen7", EntityContext.Gen7, PersonalTable.USUM), ("gen7b", EntityContext.Gen7b, PersonalTable.GG), ("gen8", EntityContext.Gen8, PersonalTable.SWSH),
      ("gen8a", EntityContext.Gen8a, PersonalTable.LA), ("gen8b", EntityContext.Gen8b, PersonalTable.BDSP), ("gen9", EntityContext.Gen9, PersonalTable.SV),
      ("gen9a", EntityContext.Gen9a, PersonalTable.ZA) };
    var evo = new Dictionary<string, object>();
    var items = new Dictionary<string, string[]>();
    var moveinfo = new Dictionary<string, object>();
    foreach (var (id, ctx, t) in ctxs) {
      var tree = EvolutionTree.GetEvolutionTree(ctx);
      var rows = new List<object>();
      for (ushort s = 1; s <= t.MaxSpeciesID; s++) {
        int fc = Math.Max((int)t.GetFormEntry(s, 0).FormCount, 1);
        for (byte f = 0; f < fc; f++) {
          var fw = tree.Forward.GetForward(s, f).Span;
          foreach (var m in fw) {
            if (m.Method == EvolutionType.None) continue;
            rows.Add(new { species = s, form = f, to_species = m.Species, to_form = m.GetDestinationForm(f), method = m.Method.ToString(), method_id = (int)m.Method, argument = m.Argument, level = m.Level, level_up = m.LevelUp });
          }
        }
      }
      evo[id] = rows;
      var ver = ctx switch { EntityContext.Gen3 => GameVersion.E, EntityContext.Gen4 => GameVersion.HGSS, _ => GameVersion.Any };
      try { items[id] = en.GetItemStrings(ctx, ver); } catch { items[id] = en.itemlist; }
      var types = MoveInfo.GetTypeTable(ctx).ToArray();
      var pp = MoveInfo.GetPPTable(ctx).ToArray();
      byte[] dummied = Array.Empty<byte>();
      try { dummied = MoveInfo.GetDummiedMovesHashSet(ctx).ToArray(); } catch { }
      var dl = new List<int>();
      for (int mv = 0; mv < types.Length; mv++) if (dummied.Length > 0 && MoveInfo.IsDummiedMove(dummied, (ushort)mv)) dl.Add(mv);
      moveinfo[id] = new { types, pp, dummied = dl };
      Console.WriteLine($"evo/moveinfo {id}: {rows.Count}");
    }
    File.WriteAllText(Path.Combine(outDir, "evolutions.json"), JsonSerializer.Serialize(evo));
    File.WriteAllText(Path.Combine(outDir, "items_en.json"), JsonSerializer.Serialize(items));
    File.WriteAllText(Path.Combine(outDir, "moveinfo.json"), JsonSerializer.Serialize(moveinfo));
    // move + item names in 10 languages
    var mn = new Dictionary<string, object>();
    foreach (var l in Langs) { var gs = GameInfo.GetStrings(l); mn[l] = new { moves = gs.movelist, items = gs.itemlist }; }
    File.WriteAllText(Path.Combine(outDir, "names_moves_items.json"), JsonSerializer.Serialize(mn));

    // ---- machines per game (label, move)
    var mach = new Dictionary<string, List<object>>();
    void M(string g, string prefix, IEnumerable<ushort> moves, int start = 1) {
      if (!mach.ContainsKey(g)) mach[g] = new List<object>();
      int i = start; foreach (var mv in moves) { mach[g].Add(new { label = $"{prefix}{i:00}", move = mv }); i++; }
    }
    var g1 = PersonalInfo1.MachineMoves.ToArray().Select(b => (ushort)b).ToArray();
    M("rb", "TM", g1.Take(50)); M("rb", "HM", g1.Skip(50));
    M("y", "TM", g1.Take(50)); M("y", "HM", g1.Skip(50));
    var g2 = PersonalInfo2.MachineMoves.ToArray().Select(b => (ushort)b).ToArray();
    foreach (var g in new[] { "gs", "c" }) { M(g, "TM", g2.Take(50)); M(g, "HM", g2.Skip(50).Take(7)); }
    foreach (var g in new[] { "rs", "e", "frlg" }) { M(g, "TM", PersonalInfo3.MachineMovesTechnical.ToArray()); M(g, "HM", PersonalInfo3.MachineMovesHidden.ToArray()); }
    foreach (var g in new[] { "dp", "pt" }) { M(g, "TM", PersonalInfo4.MachineMovesTechnical.ToArray()); M(g, "HM", PersonalInfo4.MachineMovesHiddenDPPt.ToArray()); }
    M("hgss", "TM", PersonalInfo4.MachineMovesTechnical.ToArray()); M("hgss", "HM", PersonalInfo4.MachineMovesHiddenHGSS.ToArray());
    var g5 = PersonalInfo5BW.MachineMoves.ToArray();
    foreach (var g in new[] { "bw", "b2w2" }) { M(g, "TM", g5.Take(95)); M(g, "HM", g5.Skip(95)); }
    var g6x = LearnSource6XY.MachineMoves.ToArray(); M("xy", "TM", g6x.Take(100)); M("xy", "HM", g6x.Skip(100));
    var g6a = LearnSource6AO.MachineMoves.ToArray(); M("oras", "TM", g6a.Take(100)); M("oras", "HM", g6a.Skip(100));
    var g7 = PersonalInfo7.MachineMoves.ToArray(); M("sm", "TM", g7); M("usum", "TM", g7);
    M("lgpe", "TM", LearnSource7GG.MachineMoves.ToArray());
    M("sw", "TM", PersonalInfo8SWSH.MachineMovesTechnical.ToArray(), 0); M("sw", "TR", PersonalInfo8SWSH.MachineMovesRecord.ToArray(), 0);
    M("bdsp", "TM", PersonalInfo8BDSP.MachineMoves.ToArray());
    M("sv", "TM", PersonalInfo9SV.MachineMoves.ToArray());
    M("za", "TM", PersonalInfo9ZA.MachineMoves.ToArray());
    File.WriteAllText(Path.Combine(outDir, "machines.json"), JsonSerializer.Serialize(mach));
    Console.WriteLine("machines ok");

    // ---- learnsets per game (level-up, egg, machine, reminder, mastery/shop, plus)
    Learn.Run(outDir);
  }
}
