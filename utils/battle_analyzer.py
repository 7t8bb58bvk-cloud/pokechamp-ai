class BattleAnalyzer:
    @staticmethod
    def summarize(result):
        print("=" * 40)
        print("Battle Result")
        print("=" * 40)
        print("Winner :", result["winner"])
        print("Turns  :", result["turns"])
        print("Log len:", len(result.get("history", [])))
        return {
            "winner": result["winner"],
            "turns": result["turns"],
            "log_len": len(result.get("history", [])),
        }
