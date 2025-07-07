import pyxel
import random

# 画面サイズ
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

# 星の数 (基本の数を100にしました)
STAR_COUNT = 100
DENSE_STAR_COUNT = 400  # 高密度エリアの星の数

# プレイヤーの初期位置
PLAYER_INITIAL_X = SCREEN_WIDTH / 2
PLAYER_INITIAL_Y = 200

# プレイヤーの色
PLAYER_COLOR = 7  # 白
PLAYER_TRAIL_COLOR = 6  # 軌跡の色（紫）

# パーティクルの数
PARTICLE_COUNT = 15


class Game:
    """
    ゲーム本体を管理するクラス
    """

    def __init__(self):
        """
        ゲームの初期化
        """
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="天にあまねくMilky Way", fps=60)

        # ゲームの状態を管理（TITLE, PLAYING, GAMEOVER, COMPLETE）
        self.scene = "TITLE"

        # ゲームの初期状態を設定
        self.reset()

        # Pyxelの実行開始
        pyxel.run(self.update, self.draw)

    def reset(self):
        """
        ゲームの状態を初期値にリセットする
        """
        # プレイヤーの位置
        self.player_x = PLAYER_INITIAL_X
        self.player_y = PLAYER_INITIAL_Y

        # プレイヤーの速度（慣性用）
        self.player_vx = 0

        # プレイヤーの軌跡を保存するリスト
        self.player_trail = []

        # 星のリストを初期化
        self.stars = []
        self._add_stars(STAR_COUNT)  # 基本の星を生成

        # スクロール速度の基本値
        self.scroll_speed = 0.8  # 初速を0.8に調整

        # ゲーム開始からのフレーム数
        self.frame_count = 0

        # --- ダメージシステムの変数を初期化 ---
        self.damage = 0

        # --- パーティクルシステムの変数を初期化 ---
        self.particles = []

        # --- 高密度エリア関連の変数を初期化 ---
        self.is_dense_zone = False
        # 次の高密度エリアが開始するY座標
        self.next_dense_zone_trigger_y = PLAYER_INITIAL_Y - 50
        # 現在の高密度エリアが終了するY座標
        self.current_dense_zone_end_y = 0

    def _add_stars(self, count):
        """指定された数の星をリストに追加するヘルパー関数"""
        for _ in range(count):
            self.stars.append(
                [
                    random.uniform(0, SCREEN_WIDTH),
                    random.uniform(0, -SCREEN_HEIGHT),  # 画面の上から登場させる
                    random.randint(8, 14),  # レインボーカラーの範囲
                    random.uniform(0.7, 1.5),  # 星ごとの固有速度
                ]
            )

    def _create_particles(self, x, y):
        """指定した位置にパーティクルを生成する"""
        for _ in range(PARTICLE_COUNT):
            # [x, y, vx, vy, life, color]
            self.particles.append(
                [
                    x,
                    y,
                    random.uniform(-1.5, 1.5),
                    random.uniform(-1.5, 1.5),
                    random.randint(20, 40),
                    random.choice([7, 8, 10]),  # 白、赤、黄
                ]
            )

    def update(self):
        """
        フレームごとの状態更新
        """
        # 現在のシーンに応じて処理を分岐
        if self.scene == "TITLE":
            self.update_title_scene()
        elif self.scene == "PLAYING":
            self.update_playing_scene()
        elif self.scene == "GAMEOVER" or self.scene == "COMPLETE":
            self.update_end_scene()

    def update_title_scene(self):
        """
        タイトル画面の更新処理
        """
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.scene = "PLAYING"

    def update_playing_scene(self):
        """
        ゲームプレイ中の更新処理
        """
        self.frame_count += 1

        # --- 高密度エリアの管理 ---
        if not self.is_dense_zone and self.player_y <= self.next_dense_zone_trigger_y:
            self.is_dense_zone = True
            self.current_dense_zone_end_y = self.next_dense_zone_trigger_y - 50
            self.next_dense_zone_trigger_y = self.current_dense_zone_end_y - 50
            self._add_stars(DENSE_STAR_COUNT - STAR_COUNT)

        if self.is_dense_zone and self.player_y <= self.current_dense_zone_end_y:
            self.is_dense_zone = False
            self.stars = self.stars[:STAR_COUNT]

        # --- プレイヤーの更新 ---
        target_x = pyxel.mouse_x
        acceleration = (target_x - self.player_x) * 0.02
        self.player_vx += acceleration
        self.player_vx *= 0.9
        self.player_x += self.player_vx
        self.player_x = max(0, min(SCREEN_WIDTH - 1, self.player_x))

        # --- 難易度とプレイヤーの上昇 ---
        self.scroll_speed = 0.8 + self.frame_count / 900
        self.player_y -= 0.02 * self.scroll_speed

        # --- 軌跡の更新 ---
        for point in self.player_trail:
            point[1] += self.scroll_speed
        self.player_trail.append([self.player_x, self.player_y])
        self.player_trail = [p for p in self.player_trail if p[1] < SCREEN_HEIGHT]

        # --- 星の更新 ---
        for star in self.stars:
            star[1] += star[3] * self.scroll_speed
            if star[1] >= SCREEN_HEIGHT:
                star[1] -= SCREEN_HEIGHT * 1.5
                star[0] = random.uniform(0, SCREEN_WIDTH)

        # --- パーティクルの更新 ---
        for p in self.particles:
            p[0] += p[2]  # x移動
            p[1] += p[3]  # y移動
            p[3] += 0.1  # 重力
            p[4] -= 1  # 寿命を減らす
        # 寿命が尽きたパーティクルを削除
        self.particles = [p for p in self.particles if p[4] > 0]

        # --- 当たり判定 ---
        player_rect = (self.player_x - 1, self.player_y - 1, 2, 2)
        for star in self.stars:
            x, y, color, speed = star
            if (
                player_rect[0] < x < player_rect[0] + player_rect[2]
                and player_rect[1] < y < player_rect[1] + player_rect[3]
            ):
                self.damage += 5  # 5ダメージに変更
                self._create_particles(self.player_x, self.player_y)  # パーティクル生成
                pyxel.play(3, 7)  # 被ダメージ音

                star[1] = SCREEN_HEIGHT + 10

                if self.damage >= 100:
                    self.scene = "GAMEOVER"
                    pyxel.play(3, 8)
                    return

        # --- ゲームクリア判定 ---
        if self.player_y <= 0:
            self.scene = "COMPLETE"
            pyxel.play(3, 14)

    def update_end_scene(self):
        """
        ゲームオーバー/コンプリート画面の更新処理
        """
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.reset()
            self.scene = "TITLE"

    def draw(self):
        """
        フレームごとの描画処理
        """
        pyxel.cls(0)
        self.draw_stars()
        self.draw_particles()  # パーティクルを描画

        if self.scene == "TITLE":
            self.draw_title_scene()
        elif self.scene == "PLAYING":
            self.draw_playing_scene()
        elif self.scene == "GAMEOVER":
            self.draw_gameover_scene()
        elif self.scene == "COMPLETE":
            self.draw_complete_scene()

    def draw_stars(self):
        """
        星空を描画する
        """
        for x, y, color, speed in self.stars:
            if random.randint(0, 29) == 0:
                pyxel.pset(x, y, 7)
            else:
                pyxel.pset(x, y, color)

    def draw_particles(self):
        """パーティクルを描画する"""
        for x, y, vx, vy, life, color in self.particles:
            pyxel.pset(x, y, color)

    def draw_title_scene(self):
        """
        タイトル画面の描画
        """
        title_text = "TEN NI AMANEKU MILKY WAY"
        pyxel.text((SCREEN_WIDTH - len(title_text) * 4) / 2, 100, title_text, 7)

        start_text = "- CLICK TO START -"
        pyxel.text(
            (SCREEN_WIDTH - len(start_text) * 4) / 2,
            140,
            start_text,
            pyxel.frame_count % 16,
        )

    def draw_playing_scene(self):
        """
        ゲームプレイ中の描画
        """
        for x, y in self.player_trail:
            pyxel.pset(x, y, PLAYER_TRAIL_COLOR)
        pyxel.pset(self.player_x, self.player_y, PLAYER_COLOR)

        if self.is_dense_zone:
            text = "DENSE ZONE"
            pyxel.text(
                (SCREEN_WIDTH - len(text) * 4) / 2, 5, text, pyxel.frame_count % 16
            )

        damage_text = f"DAMAGE: {self.damage}"
        pyxel.text(5, 5, damage_text, 8)

        rest_y_text = f"REST: {int(self.player_y)}"
        text_x = SCREEN_WIDTH - len(rest_y_text) * 4 - 5
        pyxel.text(text_x, 5, rest_y_text, 7)

    def draw_gameover_scene(self):
        """
        ゲームオーバー画面の描画
        """
        text = "GAME OVER"
        pyxel.text((SCREEN_WIDTH - len(text) * 4) / 2, 110, text, 8)

        restart_text = "- CLICK TO RESTART -"
        pyxel.text((SCREEN_WIDTH - len(restart_text) * 4) / 2, 140, restart_text, 7)

    def draw_complete_scene(self):
        """
        ゲームクリア画面の描画
        """
        damage_text = f"DAMAGE: {self.damage}"
        pyxel.text(5, 5, damage_text, 8)

        rest_y_text = f"REST: {max(0, int(self.player_y))}"
        text_x = SCREEN_WIDTH - len(rest_y_text) * 4 - 5
        pyxel.text(text_x, 5, rest_y_text, 7)

        text = "COMPLETE!"
        pyxel.text((SCREEN_WIDTH - len(text) * 4) / 2, 110, text, 11)

        restart_text = "- CLICK TO RESTART -"
        pyxel.text((SCREEN_WIDTH - len(restart_text) * 4) / 2, 140, restart_text, 7)


# ゲームクラスのインスタンスを作成して実行
Game()
