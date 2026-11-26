using System.Text.Json;
using PKHeX.Core;

public static class Learn {
  record Row(ushort species, byte form, string method, ushort move, int level);

  static void AddLevel(List<Row> r, ushort s, byte f, Learnset ls, string method = "level-up") {
    if (ls is null) return;
    var mv = ls.GetAllMoves(); var lv = ls.GetAllLevels();
    for (int i = 0; i < mv.Length; i++) r.Add(new Row(s, f, method, mv[i], lv[i]));
  }
  static void AddList(List<Row> r, ushort s, byte f, ReadOnlySpan<ushort> moves, string method) {
    foreach (var m in moves) if (m != 0) r.Add(new Row(s, f, method, m, 0));
  }
  delegate void AllMoves(Span<bool> result, PKM pk, EvoCriteria evo, MoveSourceType types);
  // Tutors read through PKHeX's own learn sources (type, special and "enhanced" tutors): Gen 3 (E, FR/LG), 6 and 7.
  static void AddTutors(List<Row> r, ushort s, byte f, PKM pk, AllMoves all, MoveSourceType types = MoveSourceType.TypeTutor | MoveSourceType.SpecialTutor) {
    var res = new bool[1000]; pk.Species = s; pk.Form = f;
    try { all(res, pk, new EvoCriteria { Species = s, Form = f, LevelMax = 100, LevelMin = 1 }, types); }
    catch (IndexOutOfRangeException) when (f != 0) {
      // some alternate-form entries carry no tutor flags: forms share the species' tutor compatibility
      pk.Form = 0; Array.Clear(res); all(res, pk, new EvoCriteria { Species = s, Form = 0, LevelMax = 100, LevelMin = 1 }, types);
    }
    for (int m = 1; m < res.Length; m++) if (res[m]) r.Add(new Row(s, f, "tutor", (ushort)m, 0));
  }
  static readonly HashSet<ushort> FRLGTutors = [5, 14, 25, 34, 38, 68, 69, 86, 102, 118, 135, 138, 153, 157, 164];
  static void AddTM(List<Row> r, ushort s, byte f, Func<int, bool> can, ReadOnlySpan<ushort> moves, string method = "machine") {
    for (int i = 0; i < moves.Length; i++) { bool ok; try { ok = can(i); } catch (IndexOutOfRangeException) { ok = false; } if (moves[i] != 0 && ok) r.Add(new Row(s, f, method, moves[i], 0)); }
  }

  public static void Run(string outDir) {
    var games = new (string id, IPersonalTable t)[] {
      ("rb", PersonalTable.RB), ("y", PersonalTable.Y), ("gs", PersonalTable.GS), ("c", PersonalTable.C), ("rs", PersonalTable.RS), ("e", PersonalTable.E),
      ("fr", PersonalTable.FR), ("lg", PersonalTable.LG), ("dp", PersonalTable.DP), ("pt", PersonalTable.Pt), ("hgss", PersonalTable.HGSS),
      ("bw", PersonalTable.BW), ("b2w2", PersonalTable.B2W2), ("xy", PersonalTable.XY), ("oras", PersonalTable.AO), ("sm", PersonalTable.SM),
      ("usum", PersonalTable.USUM), ("lgpe", PersonalTable.GG), ("sw", PersonalTable.SWSH), ("bdsp", PersonalTable.BDSP), ("la", PersonalTable.LA),
      ("sv", PersonalTable.SV), ("za", PersonalTable.ZA) };
    foreach (var (g, t) in games) {
      var r = new List<Row>();
      for (ushort s = 1; s <= t.MaxSpeciesID; s++) {
        int fc = Math.Max((int)t.GetFormEntry(s, 0).FormCount, 1);
        for (byte f = 0; f < fc; f++) {
          if (!t.IsPresentInGame(s, f)) continue;
          var p = t.GetFormEntry(s, f);
          switch (g) {
            case "rb": AddLevel(r, s, f, LearnSource1RB.Instance.GetLearnset(s, f)); { var pi = (PersonalInfo1)p; var mm = PersonalInfo1.MachineMoves; for (int i = 0; i < mm.Length; i++) if (pi.GetIsLearnTM(i)) r.Add(new Row(s, f, "machine", mm[i], 0)); var init = new ushort[4]; pi.GetMoves(init); AddList(r, s, f, init, "level-up-1"); } break;
            case "y": AddLevel(r, s, f, LearnSource1YW.Instance.GetLearnset(s, f)); { var pi = (PersonalInfo1)p; var mm = PersonalInfo1.MachineMoves; for (int i = 0; i < mm.Length; i++) if (pi.GetIsLearnTM(i)) r.Add(new Row(s, f, "machine", mm[i], 0)); var init = new ushort[4]; pi.GetMoves(init); AddList(r, s, f, init, "level-up-1"); } break;
            case "gs": AddLevel(r, s, f, LearnSource2GS.Instance.GetLearnset(s, f)); AddList(r, s, f, LearnSource2GS.Instance.GetEggMoves(s, f), "egg"); { var pi = (PersonalInfo2)p; var mm = PersonalInfo2.MachineMoves; for (int i = 0; i < mm.Length; i++) if (pi.GetIsLearnTM(i)) r.Add(new Row(s, f, "machine", mm[i], 0)); } break;
            case "c": AddLevel(r, s, f, LearnSource2C.Instance.GetLearnset(s, f)); AddList(r, s, f, LearnSource2C.Instance.GetEggMoves(s, f), "egg"); { var pi = (PersonalInfo2)p; var mm = PersonalInfo2.MachineMoves; for (int i = 0; i < mm.Length; i++) if (pi.GetIsLearnTM(i)) r.Add(new Row(s, f, "machine", mm[i], 0));
              // Crystal: Goldenrod move tutor (Flamethrower, Ice Beam, Thunderbolt)
              var tu = PersonalInfo2.TutorMoves; for (int i = 0; i < tu.Length; i++) if (pi.GetIsLearnTutorType(i)) r.Add(new Row(s, f, "tutor", tu[i], 0)); } break;
            case "rs": case "e": case "fr": case "lg": {
              Learnset ls = g switch { "rs" => LearnSource3RS.Instance.GetLearnset(s, f), "e" => LearnSource3E.Instance.GetLearnset(s, f), "fr" => LearnSource3FR.Instance.GetLearnset(s, f), _ => LearnSource3LG.Instance.GetLearnset(s, f) };
              AddLevel(r, s, f, ls);
              var egg = g switch { "rs" => LearnSource3RS.Instance.GetEggMoves(s, f), "e" => LearnSource3E.Instance.GetEggMoves(s, f), "fr" => LearnSource3FR.Instance.GetEggMoves(s, f), _ => LearnSource3LG.Instance.GetEggMoves(s, f) };
              AddList(r, s, f, egg, "egg");
              var pi = (PersonalInfo3)p; var tm = PersonalInfo3.MachineMovesTechnical; var hm = PersonalInfo3.MachineMovesHidden;
              for (int i = 0; i < tm.Length; i++) if (pi.TMHM[i]) r.Add(new Row(s, f, "machine", tm[i], 0));
              for (int i = 0; i < hm.Length; i++) if (pi.TMHM[tm.Length + i]) r.Add(new Row(s, f, "machine", hm[i], 0));
              // R/S have no in-game tutor (PKHeX's R/S source also carries the Colosseum/XD tutors: not R/S data)
              if (g == "e") AddTutors(r, s, f, new PK3(), LearnSource3E.Instance.GetAllMoves);
              if (g == "fr" || g == "lg") { // FR/LG tutors = the 15 moves shared with Emerald's list, same compatibility flags
                var te = new bool[1000]; var pk3 = new PK3 { Species = s };
                LearnSource3E.Instance.GetAllMoves(te, pk3, new EvoCriteria { Species = s, Form = 0, LevelMax = 100, LevelMin = 1 }, MoveSourceType.TypeTutor | MoveSourceType.SpecialTutor);
                foreach (var m in FRLGTutors) if (te[m]) r.Add(new Row(s, f, "tutor", m, 0));
                AddTutors(r, s, f, new PK3(), g == "fr" ? LearnSource3FR.Instance.GetAllMoves : LearnSource3LG.Instance.GetAllMoves); }
              break; }
            case "dp": case "pt": case "hgss": {
              Learnset ls = g switch { "dp" => LearnSource4DP.Instance.GetLearnset(s, f), "pt" => LearnSource4Pt.Instance.GetLearnset(s, f), _ => LearnSource4HGSS.Instance.GetLearnset(s, f) };
              AddLevel(r, s, f, ls);
              var egg = g switch { "dp" => LearnSource4DP.Instance.GetEggMoves(s, f), "pt" => LearnSource4Pt.Instance.GetEggMoves(s, f), _ => LearnSource4HGSS.Instance.GetEggMoves(s, f) };
              AddList(r, s, f, egg, "egg");
              var pi = (PersonalInfo4)p; var tm = PersonalInfo4.MachineMovesTechnical; var hm = g == "hgss" ? PersonalInfo4.MachineMovesHiddenHGSS : PersonalInfo4.MachineMovesHiddenDPPt;
              for (int i = 0; i < tm.Length; i++) if (pi.GetIsLearnTM(i)) r.Add(new Row(s, f, "machine", tm[i], 0));
              for (int i = 0; i < hm.Length; i++) if (pi.GetIsLearnHM(i)) r.Add(new Row(s, f, "machine", hm[i], 0));
              // special tutors of D/P/Pt/HG/SS (ultimate moves, Draco Meteor)
              {
                if (PersonalInfo4.SpecialTutorBlastBurn.Contains(s)) r.Add(new Row(s, f, "tutor", 307, 0));
                if (PersonalInfo4.SpecialTutorHydroCannon.Contains(s)) r.Add(new Row(s, f, "tutor", 308, 0));
                if (PersonalInfo4.SpecialTutorFrenzyPlant.Contains(s)) r.Add(new Row(s, f, "tutor", 338, 0));
                if (PersonalInfo4.SpecialTutorDracoMeteor.Contains(s)) r.Add(new Row(s, f, "tutor", 434, 0)); }
              if (g != "dp") {
                // Pt/HG/SS tutors: PKHeX stores one compatibility table (HG/SS personal entries, PersonalInfo4.TutorMoves);
                // its first 38 entries are the Platinum tutors, the last 14 were added in HG/SS
                var hg = (PersonalInfo4)PersonalTable.HGSS.GetFormEntry(s, f); var tu = PersonalInfo4.TutorMoves;
                int n = g == "pt" ? 38 : tu.Length;
                for (int i = 0; i < n && i < hg.TypeTutors.Length; i++) if (hg.TypeTutors[i]) r.Add(new Row(s, f, "tutor", tu[i], 0)); }
              break; }
            case "bw": case "b2w2": {
              AddLevel(r, s, f, g == "bw" ? LearnSource5BW.Instance.GetLearnset(s, f) : LearnSource5B2W2.Instance.GetLearnset(s, f));
              AddList(r, s, f, g == "bw" ? LearnSource5BW.Instance.GetEggMoves(s, f) : LearnSource5B2W2.Instance.GetEggMoves(s, f), "egg");
              var pi = (IPersonalInfoTM)p; AddTM(r, s, f, pi.GetIsLearnTM, PersonalInfo5BW.MachineMoves);
              var pt5 = (IPersonalInfoTutorType)p; AddTM(r, s, f, pt5.GetIsLearnTutorType, PersonalInfo5BW.TypeTutorMoves, "tutor");
              AddTutors(r, s, f, new PK5(), g == "bw" ? LearnSource5BW.Instance.GetAllMoves : LearnSource5B2W2.Instance.GetAllMoves);
              break; }
            case "xy": { AddLevel(r, s, f, LearnSource6XY.Instance.GetLearnset(s, f)); AddList(r, s, f, LearnSource6XY.Instance.GetEggMoves(s, f), "egg");
              var pi = (PersonalInfo6XY)p; AddTM(r, s, f, pi.GetIsLearnTM, LearnSource6XY.MachineMoves); AddTutors(r, s, f, new PK6(), LearnSource6XY.Instance.GetAllMoves); break; }
            case "oras": { AddLevel(r, s, f, LearnSource6AO.Instance.GetLearnset(s, f)); AddList(r, s, f, LearnSource6AO.Instance.GetEggMoves(s, f), "egg");
              var pi = (PersonalInfo6AO)p; AddTM(r, s, f, pi.GetIsLearnTM, LearnSource6AO.MachineMoves); AddTutors(r, s, f, new PK6(), LearnSource6AO.Instance.GetAllMoves); break; }
            case "sm": case "usum": {
              AddLevel(r, s, f, g == "sm" ? LearnSource7SM.Instance.GetLearnset(s, f) : LearnSource7USUM.Instance.GetLearnset(s, f));
              AddList(r, s, f, g == "sm" ? LearnSource7SM.Instance.GetEggMoves(s, f) : LearnSource7USUM.Instance.GetEggMoves(s, f), "egg");
              var pi = (PersonalInfo7)p; AddTM(r, s, f, pi.GetIsLearnTM, PersonalInfo7.MachineMoves);
              if (g == "usum") AddTM(r, s, f, pi.GetIsLearnTutorSpecial, PersonalInfo7.BattlePointTutorMoves, "tutor");
              AddTutors(r, s, f, new PK7(), g == "sm" ? LearnSource7SM.Instance.GetAllMoves : LearnSource7USUM.Instance.GetAllMoves);
              break; }
            case "lgpe": { AddLevel(r, s, f, LearnSource7GG.Instance.GetLearnset(s, f)); var pi = (PersonalInfo7GG)p; AddTM(r, s, f, pi.GetIsLearnTM, LearnSource7GG.MachineMoves); break; }
            case "sw": { AddLevel(r, s, f, LearnSource8SWSH.Instance.GetLearnset(s, f)); AddList(r, s, f, LearnSource8SWSH.Instance.GetEggMoves(s, f), "egg");
              var pi = (PersonalInfo8SWSH)p; AddTM(r, s, f, pi.GetIsLearnTM, PersonalInfo8SWSH.MachineMovesTechnical);
              var tr = PersonalInfo8SWSH.MachineMovesRecord; for (int i = 0; i < tr.Length; i++) if (pi.GetIsLearnTR(i)) r.Add(new Row(s, f, "machine", tr[i], 0));
              AddTM(r, s, f, pi.GetIsLearnTutorType, PersonalInfo8SWSH.TypeTutorMoves, "tutor"); AddTM(r, s, f, pi.GetIsLearnTutorSpecial, PersonalInfo8SWSH.SpecialTutorMoves, "tutor"); break; }
            case "bdsp": { AddLevel(r, s, f, LearnSource8BDSP.Instance.GetLearnset(s, f)); AddList(r, s, f, LearnSource8BDSP.Instance.GetEggMoves(s, f), "egg");
              var pi = (PersonalInfo8BDSP)p; AddTM(r, s, f, pi.GetIsLearnTM, PersonalInfo8BDSP.MachineMoves); AddTM(r, s, f, pi.GetIsLearnTutorType, PersonalInfo8BDSP.TypeTutorMoves, "tutor"); break; }
            case "la": { var (lv, mastery) = LearnSource8LA.GetLearnsetAndMastery(s, f); AddLevel(r, s, f, lv); AddLevel(r, s, f, mastery, "mastery");
              var pi = (PersonalInfo8LA)p; for (int i = 0; i < pi.GetMoveShopCount(); i++) { int idx = pi.GetMoveShopIndex(i); if (pi.GetIsLearnMoveShop((ushort)PersonalInfo8LA.GetMoveShopMove(idx))) r.Add(new Row(s, f, "tutor", PersonalInfo8LA.GetMoveShopMove(idx), 0)); } break; }
            case "sv": { AddLevel(r, s, f, LearnSource9SV.Instance.GetLearnset(s, f)); AddList(r, s, f, LearnSource9SV.Instance.GetEggMoves(s, f), "egg"); AddList(r, s, f, LearnSource9SV.Instance.GetReminderMoves(s, f), "reminder");
              var pi = (PersonalInfo9SV)p; AddTM(r, s, f, pi.GetIsLearnTM, PersonalInfo9SV.MachineMoves); break; }
            case "za": { var (lv, plus) = LearnSource9ZA.GetLearnsetAndPlus(s, f); AddLevel(r, s, f, lv); AddLevel(r, s, f, plus, "plus");
              var pi = (PersonalInfo9ZA)p; AddTM(r, s, f, pi.GetIsLearnTM, PersonalInfo9ZA.MachineMoves); break; }
          }
        }
      }
      File.WriteAllText(Path.Combine(outDir, $"learnset_{g}.json"), JsonSerializer.Serialize(r.Select(x => new object[] { x.species, x.form, x.method, x.move, x.level })));
      Console.WriteLine($"learnset {g}: {r.Count}");
    }
  }
}
