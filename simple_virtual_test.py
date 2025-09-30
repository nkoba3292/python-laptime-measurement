# simple_virtual_test.py
# -*- coding: utf-8 -*-
"""
シンプルな仮想テストシステム（コマンドライン版）
依存関係を最小限にしたバージョン
"""
import time
import json
from datetime import datetime
from pathlib import Path

class SimpleLapTimeTest:
    def __init__(self):
        self.lap_times = []
        self.start_time = None
        self.current_lap = 0
        self.max_laps = 3
        self.race_started = False
        self.race_finished = False
        self.show_timer = True
        
        # データ保存
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def display_system_info(self):
        """システム情報の表示"""
        print("\n🏁 自動運転ミニカー予選タイム計測システム")
        print("=" * 60)
        print("📋 システム仕様:")
        print("  • LOGICOOL C270 x2台デュアルカメラ")
        print("  • 俯瞰カメラ: 1280x720 (メイン表示)")
        print("  • スタートラインカメラ: 427x240 (左下1/9)")
        print("  • 自動スタートライン検出")
        print("  • 3周ラップタイム計測")
        print("  • 効果音再生（スタート/ゴール）")
        print("  • リアルタイム表示")
        print("  • 自動データ保存")
        print("=" * 60)
    
    def show_camera_layout(self):
        """カメラレイアウトの表示"""
        print("\n📹 カメラ表示レイアウト:")
        print("┌─────────────────────────────────────┐")
        print("│  俯瞰カメラ (1280x720)              │")
        print("│  コース全体監視                      │")
        print("│                                    │")
        print("│  ┌─────────┐                      │")
        print("│  │スタートライン│  ラップタイム表示    │")
        print("│  │カメラ(小窓)│  現在ラップ: X/3      │")
        print("│  │427x240   │  タイム: XX.XX秒      │")
        print("│  └─────────┘  ラップ履歴...        │")
        print("└─────────────────────────────────────┘")
    
    def interactive_race_simulation(self):
        """インタラクティブなレースシミュレーション"""
        print("\n🎮 仮想レーステスト開始")
        print("=" * 60)
        print("操作方法:")
        print("• Enterキーを押すとスタートライン通過をシミュレート")
        print("• 'q'を入力して終了")
        print("• 'r'を入力してレースリセット")
        print("=" * 60)
        
        while True:
            self.display_race_status()
            
            if self.race_finished:
                print("\n🏆 レース完了! 新しいレースを開始するには'r'を押してください")
            elif not self.race_started:
                print("\n⏳ スタートライン通過を待機中... (Enterキーを押す)")
            else:
                print(f"\n🏃 ラップ{self.current_lap}走行中... 次のスタートライン通過でラップ完了 (Enterキー)")
            
            try:
                user_input = input(">>> ").strip().lower()
                
                if user_input == 'q':
                    print("👋 システムを終了します")
                    break
                elif user_input == 'r':
                    self.reset_race()
                elif user_input == '' and not self.race_finished:
                    self.handle_start_line_crossing()
                else:
                    print("❓ 無効な入力です")
                    
            except KeyboardInterrupt:
                print("\n👋 システム終了")
                break
    
    def display_race_status(self):
        """レース状態表示"""
        print("\n" + "="*60)
        
        if not self.race_started:
            status = "🔴 待機中"
        elif self.race_finished:
            status = "🏁 完了"
        else:
            status = f"🔴 ラップ {self.current_lap}/{self.max_laps} 走行中"
        
        print(f"状態: {status}")
        
        # タイマー表示
        if self.race_started and not self.race_finished and self.show_timer:
            current_time = time.time() - self.start_time
            minutes = int(current_time // 60)
            seconds = current_time % 60
            print(f"⏱️ 経過時間: {minutes:02d}:{seconds:05.2f}")
        elif not self.show_timer:
            print("🙈 タイマー非表示中（3周目後半）")
        
        # ラップ履歴
        if self.lap_times:
            print("📊 ラップタイム履歴:")
            for i, lap_time in enumerate(self.lap_times):
                print(f"   Lap {i+1}: {lap_time:.3f}秒")
            
            avg_time = sum(self.lap_times) / len(self.lap_times)
            best_time = min(self.lap_times)
            print(f"   平均: {avg_time:.3f}秒 | ベスト: {best_time:.3f}秒")
        
        print("="*60)
    
    def handle_start_line_crossing(self):
        """スタートライン通過処理"""
        current_time = time.time()
        
        if not self.race_started:
            # レース開始
            self.race_started = True
            self.start_time = current_time
            self.current_lap = 1
            
            print("\n🏁 レーススタート！")
            print("🎵 [スタート音再生: ピー！]")
            
        else:
            # ラップ完了
            lap_time = current_time - self.start_time
            self.lap_times.append(lap_time)
            
            print(f"\n⏱️ ラップ {len(self.lap_times)} 完了: {lap_time:.3f}秒")
            
            self.current_lap += 1
            
            # 3周目の半周でタイマー非表示
            if len(self.lap_times) == 2:  # 2周完了時
                print("🙈 次のラップ途中でタイマーを非表示にします...")
            
            # レース終了判定
            if len(self.lap_times) >= self.max_laps:
                self.race_finished = True
                total_time = sum(self.lap_times)
                
                print("\n🏁 レース完了！")
                print("🎵 [ゴール音再生: ピーピー♪]")
                print(f"🏆 総時間: {total_time:.3f}秒")
                
                self.show_final_results()
                self.save_race_data()
    
    def show_final_results(self):
        """最終結果表示"""
        if not self.lap_times:
            return
        
        total_time = sum(self.lap_times)
        avg_time = total_time / len(self.lap_times)
        best_lap = min(self.lap_times)
        worst_lap = max(self.lap_times)
        
        print("\n🏆 最終結果")
        print("=" * 40)
        print(f"総時間:     {total_time:.3f}秒")
        print(f"平均ラップ: {avg_time:.3f}秒")
        print(f"ベストラップ: {best_lap:.3f}秒")
        print(f"ワーストラップ: {worst_lap:.3f}秒")
        print("=" * 40)
        
        # ラップ別詳細
        print("📊 ラップ別詳細:")
        for i, lap_time in enumerate(self.lap_times):
            diff_from_avg = lap_time - avg_time
            mark = "🟢" if lap_time == best_lap else "🔴" if lap_time == worst_lap else "⚪"
            print(f"  {mark} Lap {i+1}: {lap_time:.3f}秒 ({diff_from_avg:+.3f}秒)")
    
    def save_race_data(self):
        """データ保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"simple_virtual_race_{timestamp}.json"
        
        race_data = {
            "timestamp": datetime.now().isoformat(),
            "test_mode": "simple_virtual",
            "lap_times": self.lap_times,
            "total_time": sum(self.lap_times) if self.lap_times else 0,
            "average_lap": sum(self.lap_times) / len(self.lap_times) if self.lap_times else 0,
            "best_lap": min(self.lap_times) if self.lap_times else 0,
            "worst_lap": max(self.lap_times) if self.lap_times else 0,
            "laps_completed": len(self.lap_times)
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(race_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 レースデータ保存完了: {filename}")
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
    
    def reset_race(self):
        """レースリセット"""
        self.lap_times.clear()
        self.start_time = None
        self.current_lap = 0
        self.race_started = False
        self.race_finished = False
        self.show_timer = True
        
        print("\n🔄 レースをリセットしました")
        print("新しいレースの準備ができました！")
    
    def run(self):
        """メイン実行"""
        self.display_system_info()
        self.show_camera_layout()
        
        print("\n🎯 このシステムの実際の動作:")
        print("1. 🚗 車両がスタートラインを通過 → 自動検出")
        print("2. ⏱️ タイマー開始・リアルタイム表示")
        print("3. 📊 各ラップのタイム記録")
        print("4. 🙈 3周目半周でタイマー非表示")
        print("5. 💾 完走後の自動データ保存")
        
        self.interactive_race_simulation()

def main():
    print("🎮 シンプル仮想テストシステム")
    print("軽量版・依存関係最小限")
    
    system = SimpleLapTimeTest()
    system.run()

if __name__ == "__main__":
    main()