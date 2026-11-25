using System.Text.Json;
using PKHeX.Core;

var tables = new (string id, IPersonalTable t, EntityContext ctx)[] {
  ("rb", PersonalTable.RB, EntityContext.Gen1), ("y", PersonalTable.Y, EntityContext.Gen1),
  ("gs", PersonalTable.GS, EntityContext.Gen2), ("c", PersonalTable.C, EntityContext.Gen2),
  ("rs", PersonalTable.RS, EntityContext.Gen3), ("e", PersonalTable.E, EntityContext.Gen3),
  ("fr", PersonalTable.FR, EntityContext.Gen3), ("lg", PersonalTable.LG, EntityContext.Gen3),
  ("dp", PersonalTable.DP, EntityContext.Gen4), ("pt", PersonalTable.Pt, EntityContext.Gen4), ("hgss", PersonalTable.HGSS, EntityContext.Gen4),
  ("bw", PersonalTable.BW, EntityContext.Gen5), ("b2w2", PersonalTable.B2W2, EntityContext.Gen5),
  ("xy", PersonalTable.XY, EntityContext.Gen6), ("oras", PersonalTable.AO, EntityContext.Gen6),
  ("sm", PersonalTable.SM, EntityContext.Gen7), ("usum", PersonalTable.USUM, EntityContext.Gen7), ("lgpe", PersonalTable.GG, EntityContext.Gen7b),
  ("sw", PersonalTable.SWSH, EntityContext.Gen8), ("bdsp", PersonalTable.BDSP, EntityContext.Gen8b), ("la", PersonalTable.LA, EntityContext.Gen8a),
  ("sv", PersonalTable.SV, EntityContext.Gen9), ("za", PersonalTable.ZA, EntityContext.Gen9a),
};
var langs = new[] { "ja", "en", "fr", "de", "it", "es", "es-419", "ko", "zh-Hans", "zh-Hant" };
var outDir = args.Length > 0 ? args[0] : "out";
Directory.CreateDirectory(outDir);
var en = GameInfo.GetStrings("en");
foreach (var (id, t, ctx) in tables) {
  var rows = new List<object>();
  for (ushort s = 1; s <= t.MaxSpeciesID; s++) {
    var b = t.GetFormEntry(s, 0);
    int fc = Math.Max((int)b.FormCount, 1);
    var formNames = FormConverter.GetFormList(s, en.Types, en.forms, GameInfo.GenderSymbolASCII, ctx);
    for (byte f = 0; f < fc; f++) {
      var p = t.GetFormEntry(s, f);
      var ab = new List<int>(); for (int i = 0; i < p.AbilityCount; i++) ab.Add(p.GetAbilityAtIndex(i));
      rows.Add(new {
        species = s, form = f, entry = t.GetFormIndex(s, f), base_entry = t.GetFormIndex(s, 0), form_name_en = f < formNames.Length ? formNames[f] : null,
        present = t.IsPresentInGame(s, f),
        hp = p.HP, atk = p.ATK, def = p.DEF, spa = p.SPA, spd = p.SPD, spe = p.SPE,
        type1 = p.Type1, type2 = p.Type2, catch_rate = p.CatchRate, base_exp = p.BaseEXP,
        ev = new[] { p.EV_HP, p.EV_ATK, p.EV_DEF, p.EV_SPA, p.EV_SPD, p.EV_SPE },
        gender = p.Gender, hatch = p.HatchCycles, friendship = p.BaseFriendship, growth = p.EXPGrowth,
        egg = new[] { p.EggGroup1, p.EggGroup2 }, abilities = ab, height = p.Height, weight = p.Weight,
        form_count = p.FormCount, dex = Dex(p)
      });
    }
  }
  File.WriteAllText(Path.Combine(outDir, $"personal_{id}.json"), JsonSerializer.Serialize(rows));
  Console.WriteLine($"{id}: {rows.Count}");
}
// names
var names = new Dictionary<string, object>();
foreach (var l in langs) {
  var gs = GameInfo.GetStrings(l);
  var forms = new Dictionary<string, string[]>();
  for (ushort s = 1; s <= 1025; s++) forms[s.ToString()] = FormConverter.GetFormList(s, gs.Types, gs.forms, GameInfo.GenderSymbolASCII, EntityContext.Gen9a);
  names[l] = new { species = gs.specieslist, types = gs.Types, abilities = gs.abilitylist, forms };
}
File.WriteAllText(Path.Combine(outDir, "names.json"), JsonSerializer.Serialize(names));
Console.WriteLine("names ok");
Extra.Run(outDir);

// ---------------------------------------------------------------- phase 1b / 2 extractions
static Dictionary<string, int> Dex(IPersonalInfo p) {
  var d = new Dictionary<string, int>();
  switch (p) {
    case PersonalInfo8SWSH x: d["galar"] = x.PokeDexIndex; d["isle-of-armor"] = x.ArmorDexIndex; d["crown-tundra"] = x.CrownDexIndex; break;
    case PersonalInfo8BDSP x: d["sinnoh"] = x.PokeDexIndex; break;
    case PersonalInfo8LA x: d["hisui"] = x.DexIndexHisui; break;
    case PersonalInfo9SV x: d["paldea"] = x.DexPaldea; d["kitakami"] = x.DexKitakami; d["blueberry"] = x.DexBlueberry; break;
    case PersonalInfo9ZA x: d["lumiose"] = x.DexIndex; break;
  }
  return d;
}
